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
from translations import TRANSLATIONS

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
    judet = db.Column(db.String(50), nullable=True) # Optional now
    localitate = db.Column(db.String(100), nullable=True) # Optional now
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
    ong_sediu = db.Column(db.String(150), default='Bucuresti, Sector 1, Str. Exemplu')
    ong_cont_bancar = db.Column(db.String(150), default='Banca Transilvania')
    signature_base64 = db.Column(db.Text, nullable=True) # allow storing signature data


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
    # Aceste coordonate sunt aproximative pentru un Formular 230 ANAF standard.
    # Necesita ajustari usoare de cativa pixeli in functie de marginea la imprimare.
    can.setFont("Helvetica-Bold", 10)
    
    # I. Date de identificare a contribuabilului
    can.drawString(65, 669, submission.nume.upper())
    can.drawString(295, 669, submission.initiala_tatalui.upper())
    can.drawString(65, 647, submission.prenume.upper())
    
    # CNP spaced out to fit exactly inside the 13 small boxes (+18.48 pitch)
    cnp_x = 352
    for char in submission.cnp:
        can.drawString(cnp_x, 660, char)
        cnp_x += 18.48
    
    # Adresa (Opțional)
    if submission.strada: can.drawString(65, 625, f"{submission.strada}")
    if submission.numar: can.drawString(288, 625, f"{submission.numar}")
    if submission.bloc: can.drawString(48, 603, f"{submission.bloc}")
    if submission.scara: can.drawString(108, 603, f"{submission.scara}")
    if submission.apartament: can.drawString(186, 603, f"{submission.apartament}")
    
    if submission.judet: can.drawString(255, 603, submission.judet.upper())
    if submission.localitate: can.drawString(65, 581, submission.localitate.upper())
    if submission.cod_postal: can.drawString(265, 581, f"{submission.cod_postal}")
    
    can.drawString(363, 597, f"{submission.telefon or ''}")
    can.drawString(363, 637, f"{submission.email or ''}")
    
    # II. Destinația sumei reprezentând până la 3.5% (Bifa)
    can.setFont("Helvetica-Bold", 12)
    can.drawString(219, 436, "X")

    can.setFont("Helvetica-Bold", 10)
    # NGO details
    can.drawString(178, 374, config.ong_name.upper() if config.ong_name else '')
    can.drawString(102, 365, config.ong_cui if config.ong_cui else '')
    can.drawString(102, 351, config.ong_iban if config.ong_iban else '')

    # Admin Signature (Semnătura împuternicitului) - aligned towards bottom right
    if config.signature_base64:
        import base64
        import tempfile
        try:
            head, b64data = config.signature_base64.split(',', 1)
            sig_data = base64.b64decode(b64data)
            with tempfile.NamedFileMode('w+b', delete=False, suffix='.png') as tmp:
                tmp.write(sig_data)
                tmp.flush()
                can.drawImage(tmp.name, 400, 50, width=120, height=45, mask='auto')
                import os
                os.remove(tmp.name)
        except Exception as e:
            print("Error drawing signature:", e)
    
    # Date today near signature
    import datetime
    can.setFont("Helvetica", 10)
    can.drawString(460, 42, datetime.datetime.now().strftime("%d.%m.%Y"))

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

@app.before_request
def set_language():
    if 'lang' not in session and not request.path.startswith('/static'):
        session['lang'] = 'en'
        ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()
            if ip in ['127.0.0.1', '::1']:
                session['lang'] = 'ro'
            else:
                try:
                    r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
                    if r.get('countryCode') == 'RO':
                        session['lang'] = 'ro'
                except:
                    pass

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'ro')
    t = TRANSLATIONS.get(lang, TRANSLATIONS['ro'])
    return dict(t=t, lang=lang)

@app.route('/lang/<lang_code>')
def set_lang_route(lang_code):
    if lang_code in TRANSLATIONS:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

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
    config.ong_sediu = request.form.get('ong_sediu')
    config.ong_cont_bancar = request.form.get('ong_cont_bancar')
    
    # Handle signature file
    sig_file = request.files.get('signature_file')
    if sig_file and sig_file.filename != '':
        import base64
        import mimetypes
        mimetype = mimetypes.guess_type(sig_file.filename)[0] or 'image/png'
        # Read file, convert to base64
        b64_encoded = base64.b64encode(sig_file.read()).decode('utf-8')
        config.signature_base64 = f"data:{mimetype};base64,{b64_encoded}"

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