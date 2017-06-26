import bll.enums
from bll.json import Json
from bll.matching import *
import dal
from dal.domain import Client, Mission, db, Skill, AppUser, Experience, Contact, Email, Phone, Application, Interview
from flask import make_response, jsonify, Response, request



@bll.app.after_request
def apply_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8100'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'X-PINGOTHER, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST,GET,PUT,DELETE,OPTIONS'
    return response


@bll.app.route('/client', methods=['GET'])
@bll.app.route('/client/<client_id>', methods=['GET'])
def list_clients(client_id=None):
    if client_id:
        return jsonify(Client.to_json(Client.query.get(client_id)))
    return jsonify({'clients': Client.list_to_json(Client.query.all())})


@bll.app.route('/client/create', methods=['POST'])
def create_client():
    print ("create client")
    jclient = request.get_json(force=True)
    print(jclient)
    client = Client.from_json(jclient)
    db.session.add(client)
    db.session.commit()

    return jsonify({})


@bll.app.route('/offer', methods=['GET'])
@bll.app.route('/offer/<offer_id>', methods=['GET'])
def list_offers(offer_id=None):
    if offer_id:
        offer = Mission.query.get(offer_id)
        matches = find_offer_match(offer.id)
        joffer = Mission.to_json(offer)
        joffer['matches'] = [AppUser.to_json(candidate) for candidate in matches]
        return jsonify(joffer)

    offers = Mission.query.filter_by(open=True).all()
    return jsonify({'offers': Mission.to_json_list(offers)})


@bll.app.route('/mission', methods=['GET'])
@bll.app.route('/mission/<mission_id>', methods=['GET'])
def list_missions(mission_id=None):
    if mission_id:
        return jsonify(Mission.to_json(Mission.query.get(mission_id)))

    missions = Mission.query.filter_by(open=False).all()
    return jsonify({'missions': Mission.to_json_list(missions)})


@bll.app.route('/mission/update', methods=['POST'])
def update_mission():
    jmission = request.get_json(force=True)
    mission_id = jmission['id'];
    mission_duration = jmission['duration']
    mission = Mission.query.get(mission_id)
    if mission and (mission.duration != mission_duration):
        mission.duration = mission_duration
        db.session.commit()

    return jsonify({})


@bll.app.route('/offer/create', methods=['POST'])
def create_offer():
    joffer = request.get_json(force=True)
    offer = Mission.from_json(joffer)
    offer.open = True
    db.session.add(offer)
    db.session.commit()
    for jskill in joffer['skills']:
        skill = Skill.from_json(jskill)
        skill.mission_id = offer.id
        db.session.add(skill)
        db.session.commit()
    return jsonify({})


@bll.app.route('/consultant', methods=['GET'])
@bll.app.route('/consultant/<consultant_id>', methods=['GET'])
def list_consultant(consultant_id=None):
    if consultant_id:
        return jsonify(AppUser.to_json(AppUser.query.get(consultant_id)))
    return jsonify({'consultants': AppUser.to_json_list(AppUser.query.filter_by(kind=bll.enums.UserType.Collaborator.name).all())})


@bll.app.route('/candidate', methods=['GET'])
@bll.app.route('/candidate/<candidate_id>', methods=['GET'])
def list_candidates(candidate_id=None):
    if candidate_id:
        candidate = AppUser.query.get(candidate_id)
        matches = find_user_match(candidate.id)
        jcandidate = AppUser.to_json(candidate)
        jcandidate["matches"] = [Mission.to_json(offer) for offer in matches]
        return jsonify(jcandidate)
    return jsonify({'candidates': AppUser.to_json_list(AppUser.query.filter_by(kind='Candidate').all())})


@bll.app.route('/candidate/create', methods=['POST'])
def create_candidate():
    jcandidate = request.get_json(force=True)
    print("Received date for create candidate: ", jcandidate)
    candidate = AppUser.from_json(jcandidate)
    candidate.kind = bll.enums.UserType.Candidate.name
    db.session.add(candidate)
    db.session.commit()
    for jskill in jcandidate['skills']:
        skill = Skill.from_json(jskill)
        skill.user_id = candidate.id
        db.session.add(skill)
        db.session.commit()

    for jexperience in jcandidate['experiences']:
        experience = Experience.from_json(jexperience)
        experience.user_id = candidate.id
        db.session.add(experience)
        db.session.commit()

    return jsonify({})


# =======================================================================================================================
@bll.app.route('/candidature', methods=['GET'])
def list_candidatures():
    return jsonify({'candidatures': [Application.to_json(application) for application in Application.query.all()]})


@bll.app.route('/candidature/<cand_id>', methods=['GET'])
def get_candidature(cand_id):
    return jsonify(Application.to_json(Application.query.get(cand_id)))


@bll.app.route('/candidature/accept/<cand_id>', methods=['GET'])
def accept_candidature(cand_id):
    application = Application.query.get(cand_id)
    application.user.mission_id = application.mission.id
    application.user.kind = bll.enums.UserType.Collaborator.name
    application.mission.open = 0
    application.accepted = 1
    db.session.commit()

    return jsonify({})


@bll.app.route('/candidature/reject/<cand_id>', methods=['GET'])
def reject_candidature(cand_id):
    application = Application.query.get(cand_id)
    application.accepted = -1
    db.session.commit()

    return jsonify({})


@bll.app.route('/candidature/create', methods=['POST'])
def create_candidature():
    japplications = request.get_json(force=True)
    print(japplications)
    offer = Mission.query.get(japplications['selectedOffer'])
    if offer:
        ids = japplications['selectedCandidates']
        for candidate_id in ids:
            print("Creating candidature with offer id:" + str(offer.id) + ", candidate id:" + str(candidate_id))
            candidate = AppUser.query.get(candidate_id)
            if candidate:
                application = Application()
                application.mission_id = offer.id
                application.user_id = candidate.id
                application.comment = ""
                db.session.add(application)
                db.session.commit()
            else:
                print("Error, candidate not found in db")

    return jsonify({})


# =======================================================================================================================
@bll.app.route("/contact/<contact_id>", methods=['GET'])
def get_contact(contact_id=None):
    contact = Contact.query.get(contact_id)
    return jsonify(Contact.to_json(contact))


@bll.app.route("/contact/create", methods=['POST'])
def create_contact():
    jcontact = request.get_json(force=True)
    print("create contact: ", jcontact)
    contact = Contact.from_json(jcontact)
    db.session.add(contact)
    db.session.commit()
    return jsonify({})


@bll.app.route('/contact/update', methods=['POST'])
def update_contact():
    jcontact = request.get_json(force=True)
    print(jcontact)
    contact = Contact.query.get(jcontact['id'])
    if contact:
        Json.from_json(contact, jcontact, ['name', 'title', 'department', 'team', 'prospection'])

        if 'emails' in jcontact:
            emails = [Email.from_json(jemail) for jemail in jcontact['emails']]
            for email in emails:
                if email.id:
                    db_entity = Email.query.get(email.id)
                    db_entity.label = email.label
                    db_entity.email = email.email
                else:
                    contact.emails.append(email)

        if 'phones' in jcontact:
            phones = [Phone.from_json(jphone) for jphone in jcontact['phones']]
            for phone in phones:
                if phone.id:
                    db_entity = Phone.query.get(phone.id)
                    db_entity.label = phone.label
                    db_entity.email = phone.phone
                else:
                    contact.phones.append(phone)

        db.session.commit()

    return jsonify({})


@bll.app.route('/interview', methods=['GET'])
def list_interviews():
    applicationId = request.args.get('application')
    print("Get list of interviews for application", applicationId)
    interviews = Interview.query.filter_by(application_id=applicationId).all()
    return jsonify({'interviews': [Interview.to_json(interview) for interview in interviews]})


@bll.app.route('/interview/<interview_id>', methods=['GET'])
def get_interview(interview_id):
    interview = Interview.query.get(interview_id)
    return jsonify(Interview.to_json(interview))


@bll.app.route('/interview/create', methods=['POST'])
def creat_interview():
    jinterview = request.get_json(force=True)
    interview = Interview.from_json(jinterview)
    if interview.title and interview.application_id:
        db.session.add(interview)
        db.session.commit()
    return jsonify({})


@bll.app.route('/interview/update', methods=['POST'])
def update_interview():
    jinterview = request.get_json(force=True)
    interview = Interview.query.get(jinterview['id'])
    Json.from_json(interview, jinterview, [
        'title',
        'creation_date',
        'interview_date',
        'interview_time',
        'notes',
        'feedback'
    ])
    db.session.commit()
    return jsonify({})


@bll.app.route('/interview/delete/<interview_id>', methods=['GET'])
def delete_interview(interview_id):
    interview = Interview.query.get(interview_id)
    db.session.delete(interview)
    db.session.commit()
    return jsonify({})


if __name__ == '__main__':
    dal.domain.db.create_all()
    bll.app.run(port=9091, debug=True)
