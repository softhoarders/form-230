import os
import io
import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///form230.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Ensure folders exist
GENERATED_DIR = os.path.join(app.root_path, 'generated_forms')
os.makedirs(GENERATED_DIR, exist_ok=True)

# Turnstile config (Use test keys or replace with real ones)
TURNSTILE_SECRET_KEY = '1x0000000000000000000000000000000AA'

# Models
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(100), nullable=False)
    prenume = db.Column(db.String(100), nullable=False)
    initiala_tatalui = db.Column(db.String(10), nullable=False)
    cnp = db.Column(db.String(20), nullable=False)
    judet = db.Column(db.String(50), nullable=False)
    localitate = db.Column(db.String(100), nullable=False)
    strada = db.Column(db.String(150), nullable=True)
    numar = db.Column(db.String(20), nullable=True)
    bloc = db.Column(db.String(20), nullable=True)
    scara = db.Column(db.String(20), nullable=True)
    apartament = db.Column(db.String(20), nullable=True)
    cod_postal = db.Column(db.String(20), nullable=True)
    telefon = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, approved
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    generated_pdf_path = db.Column(db.String(255), nullable=True)

class AdminConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ong_name = db.Column(db.String(150), default='Asociatia My NGO')
    ong_cui = db.Column(db.String(50), default='RO12345678')
    ong_iban = db.Column(db.String(50), default='RO00BANK0000000000000000')

with app.app_context():
    db.create_all()
    if not AdminConfig.query.first():
        db.session.add(AdminConfig())
        db.session.commit()

def verify_turnstile(token):
    data = {
        'secret': TURNSTILE_SECRET_KEY,
        'response': token
    }
    r = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=data)
    result = r.json()
    return result.get('success', False)

def generate_pdf(submission):
    # This assumes there is a template named form_230_template.pdf in the root directory
    template_path = os.path.join(app.root_path, 'form_230_template.pdf')
    if not os.path.exists(template_path):
        return None  # Template not found
    
    config = AdminConfig.query.first()
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    # Overlay text at specific coordinates. These coordinates need adjustment based on the actual PDF structure
    # This is a generic placement
    can.drawString(100, 700, f"{submission.nume} {submission.prenume}")
    can.drawString(100, 680, submission.cnp)
    can.drawString(100, 660, f"{submission.strada} nr {submission.numar}, bl {submission.bloc}, ap {submission.apartament}")
    can.drawString(100, 640, f"{submission.localitate}, {submission.judet}")
    
    # NGO details
    can.drawString(100, 500, config.ong_name)
    can.drawString(100, 480, config.ong_cui)
    can.drawString(100, 460, config.ong_iban)
    can.save()
    packet.seek(0)
    
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(template_path, "rb"))
    output = PdfWriter()
    
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    
    filename = f"form_{submission.id}_{submission.cnp}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "wb") as outputStream:
        output.write(outputStream)
        
    return filepath

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        turnstile_response = request.form.get('cf-turnstile-response')
        if not verify_turnstile(turnstile_response):
            flash('Verificarea Turnstile a eșuat. Încercați din nou.', 'error')
            return redirect(url_for('index'))
            
        new_sub = Submission(
            nume=request.form.get('nume'),
            prenume=request.form.get('prenume'),
            initiala_tatalui=request.form.get('initiala_tatalui'),
            cnp=request.form.get('cnp'),
            judet=request.form.get('judet'),
            localitate=request.form.get('localitate'),
            strada=request.form.get('strada'),
            numar=request.form.get('numar'),
            bloc=request.form.get('bloc'),
            scara=request.form.get('scara'),
            apartament=request.form.get('apartament'),
            cod_postal=request.form.get('cod_postal'),
            telefon=request.form.get('telefon'),
            email=request.form.get('email')
        )
        db.session.add(new_sub)
        db.session.commit()
        flash('Formularul a fost trimis cu succes!', 'success')
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'pulert' and password == 'softhoarderscnfbmuzeu':
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

def admin_required(f):
    def wrap(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/admin', methods=['GET'])
@admin_required
def admin():
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()
    config = AdminConfig.query.first()
    return render_template('admin.html', submissions=submissions, config=config)

@app.route('/admin/config', methods=['POST'])
@admin_required
def update_config():
    config = AdminConfig.query.first()
    config.ong_name = request.form.get('ong_name')
    config.ong_cui = request.form.get('ong_cui')
    config.ong_iban = request.form.get('ong_iban')
    db.session.commit()
    flash('Configurația a fost actualizată.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/approve/<int:sub_id>', methods=['POST'])
@admin_required
def approve(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    if sub.status == 'pending':
        filepath = generate_pdf(sub)
        sub.status = 'approved'
        if filepath:
            sub.generated_pdf_path = filepath
        db.session.commit()
        flash(f'Aprobare reușită pentru {sub.nume} {sub.prenume}. PDF generat.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/download/<int:sub_id>')
@admin_required
def download_pdf(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    if sub.generated_pdf_path and os.path.exists(sub.generated_pdf_path):
        return send_file(sub.generated_pdf_path, as_attachment=True)
    flash('PDF-ul nu există. Asigură-te că template-ul este prezent și formularul a fost aprobat.', 'error')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)