import urllib2
import json
import urllib

# http://<somedomain>/api?task=report&incident_title=Test&incident_description=Testing+with+the+api &incident_date=03/18/2009&incident_hour=10&incident_minute=10&incident_ampm=pm &incident_category=2,4,5,7&latitude=-1.28730007&longitude=36.82145118200820&location_name=accra &person_first=Henry+Addo&person_last=Addo&person_email=henry@ushahidi.com&resp=xml
def HTTPuploadMessages():
    
    theString = "task=report&incident_title=message.title&incident_description=message.message&incident_date=10/14/89&incident_hour=12&incident_min=34&incident_ampm=pm&category=1&latitude=-119.840798&longitude:=34.41421&location_name=message.location"    
    data = {"task":"report", "incident_title":"message.title", "incident_description":"message.message","incident_date":"2011","incident_hour":"12","incident_minute":"34","incident_ampm":"pm","incident_category":"1","latitude":"-1.28730007","longitude":"36.82145118200820","location_name":"message.location"}

    data2 = {"task":"report"}

    headers = {"Content-type": "multipart/form-data"}
    thing = urllib.urlencode(data2)

    request = urllib2.Request("http://128.111.41.47/ushahidi/api", thing, headers)
    f = urllib2.urlopen(request)
    response = f.read()
    print response
    f.close()


HTTPuploadMessages()
