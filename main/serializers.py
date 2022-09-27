from datetime import date


def serialize_meet_model(m, user_id):
    #qs = UserModel.objects.filter(id = user_id).filter(profile__quality__gt = 25).first()

    obj = {
        "id": m.id,
        "title": str(m.name),
        "start": str(m.meet_start),
        "end": str(m.meet_end),
        "url": str(m.url)
    }


    return obj