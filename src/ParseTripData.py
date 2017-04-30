# encoding: utf-8
from Trip import Trip
from workflow import Workflow, ICON_WEB, web
import datetime

class ParseTripData(object):
  def __init__(self, from_place_id, to_place_id):
    self.from_place_id = from_place_id
    self.to_place_id = to_place_id

    self.base_url = "http://reisapi.ruter.no/"
    self.from_place_name = self.get_stop_name(self.base_url, self.from_place_id)
    self.to_place_name = self.get_stop_name(self.base_url, self.to_place_id)
    self.trips = []
    self.current_time = self.get_current_time()

    self.from_place_district = self.get_district(self.base_url, self.from_place_id)
    self.to_place_district = self.get_district(self.base_url, self.to_place_id)
    
  def get_trips(self):
    self.request = self.send_request()
    self.trips = self.parse_request()
    return self.trips

  #Initiate request
  def send_request(self):
    url = self.base_url + "Travel/GetTravels?fromPlace={0}&toPlace={1}&isafter=true&time={2}".format(self.from_place_id,self.to_place_id,self.current_time)
  
    params = dict(count=20, format='json')
    response = web.get(url, params)

    #Show an error to the user if anything goes wrong
    response.raise_for_status()
    return response.json()

  def check_for_deviation(self, stages):
  	# If stage contain Deviation and contain more than [], then it is actually a deviation
		for stage in stages:
			if "Deviations" in stage and len(stage["Deviations"]):
				return True
			break

		return False

  def create_line_description(self, stages):
		
		# The first result in Stages will contain "LineNumber" unless you have to walk. A line can be bus, tram, metro or possibly train
		# Todo: Ideally it should not be like this. #Codebetter
		if "LineName" not in stages[0]:

			if "WalkingTime" in stages[0]:
				walking_time = stages[0]["WalkingTime"]
			else:
				walking_time = "x"

			if "LineName" in stages[1]:
				return "Walk %s minutes line %s " % (walking_time, stages[1]["LineName"])

			return "walk"
		
		return "Take line %s" % (stages[0]["LineName"])

  def parse_request(self):
    travelproposals = self.request['TravelProposals']

    for tp in travelproposals:
      requires_change = False
      number_of_changes_required = 0
      deviations = False

      depTime = datetime.datetime.strptime(tp['DepartureTime'], "%Y-%m-%dT%H:%M:%S")
      arrTime = datetime.datetime.strptime(tp['ArrivalTime'], "%Y-%m-%dT%H:%M:%S")
      travTime = datetime.datetime.strptime(tp['TotalTravelTime'], "%H:%M:%S")

      number_of_changes_required = len(tp['Stages']) - 1

      # Get the first line. This assumes the API returns the tram/bus/metro you should take as the first result
      line = self.create_line_description(tp['Stages'])

      #Check for deviations 
      deviations = self.check_for_deviation(tp['Stages'])

      trip = Trip(
        self.from_place_id, 
        self.to_place_id, 
        self.from_place_name, 
        self.to_place_name, 
        arrTime.strftime("%H:%M"), 
        depTime.strftime("%H:%M"), 
        travTime.strftime("%H:%M"), 
        line,
        number_of_changes_required, 
        self.current_time, 
        self.to_place_district, 
        self.from_place_district,
        deviations)

      self.trips.append(trip)
      
    return self.trips

  def get_current_time(self):
    return datetime.datetime.now().strftime("%d%m%Y%H%M%S")

  def get_stop_name(self, base_url, id):
    url = base_url +  "Place/GetStop/{0}".format(id)
    response = web.get(url)
    data = response.json()
    return data['Name']

  def get_district(self, base_url, id):
    url = base_url +  "Place/GetPlaces/{0}".format(id)
    response = web.get(url)
    data = response.json()
    return data[0]['District']