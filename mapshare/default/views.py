from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
import mapcode as mc
import json


def index(request, context="", mapcode=""):
    msg = None
    coords = (51.500675,-0.124578)
    initialZoom = 10
    if mc.isvalid(f"{context} {mapcode}"):
        coords = mc.decode(f"{context} {mapcode}")
        initialZoom = 40
    elif len(mapcode) == 0 and len(context) == 0:
        pass
    else:
        msg = f"'{context} {mapcode}' is an invalid mapcode"

    context = {
        "msg": msg,
        "urlLat": coords[0],
        "urlLng": coords[1],
        "context": context,
        "mapcode": mapcode,
        "initialZoom": initialZoom
    }
    return render(request, "index.html", context)


def getMapcodeAJAX(request):
    if request.method == "POST":
        success = False
        body = json.loads(request.body)
        response = mc.encode(body["lat"], body["lng"])
        if len(response) > 0:
            payload = [("success", "true")]
            for mapcode in response:
                payload.append((mapcode[1], mapcode[0]))
            payload = dict(payload)
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success": False}), content_type="application/json")
    else:
        return HttpResponseForbidden()