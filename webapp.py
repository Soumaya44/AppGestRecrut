import bll
import bll.enums
import dal
from flask import *
from controllers import *


@bll.app.route("/")
@bll.app.route("/index")
def index():
    if not bll.is_logged():
        return redirect(url_for('login'))
    context = Context('Welcome', 'Harington CRM')
    return render_template('layout.html', ctx=context)


@bll.app.route("/register", methods=['POST', 'GET'])
def register():
    error = ""
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        check_user = AppUser.query.filter_by(email=email).first()
        if check_user is not None:
            error = "Adresse email déjà enregistrée!"

        if password != password_confirm :
            error = "Les Mots de passe ne correspondent pas!"

        if error == "":
            password_hash = bll.make_hash(password)
            new_user = AppUser(email, password_hash)
            new_user.last_name = last_name
            new_user.first_name = first_name
            new_user.kind = bll.enums.UserType.Candidate.name
            db.session.add(new_user)
            db.session.commit()
            bll.set_session_user(new_user)
            return redirect('/user/edit/' + str(new_user.id))

    return render_template('register.html', error_msg=error)


@bll.app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_email = request.form.get('email')
        print("Checking user ", user_email)
        user = AppUser.query.filter_by(email=user_email).first()
        if user:
            bll.set_session_user(user)
            return redirect(url_for('dashboard', user_id=user.id))
        else:
            print("User not registred yet")
            return redirect(url_for('register'))

    return render_template('login.html')


@bll.app.route("/logout")
def logout():
    bll.unset_session_user()
    return redirect(url_for("login"))


if __name__ == '__main__':
    dal.domain.db.create_all()
    bll.app.run(port=9091)