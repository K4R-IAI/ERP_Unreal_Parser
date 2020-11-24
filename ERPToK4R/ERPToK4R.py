#!/usr/bin/env python

import json
import requests

def post_entity(entity, name: str, link: str, entity_send_link=''):
    resp = requests.post(link + entity_send_link,
                         data=json.dumps(entity),
                         headers={'Content-Type': 'application/json'})
    if resp.status_code == 200:
      print(name + " successfully created")
      return True
    else:
      if resp.status_code == 400:
        print("Request Body validation error")
      if resp.status_code == 500:
        print("Internal server error")
      print(name + " failed to be created, status = " +
            str(resp.status_code))
      return False

def post_shelf(shelf, store_id):
  shelf = {}
  shelf['cadPlanId'] = 'string'
  shelf['cadPlanId'] = 'string'
  shelf['depth'] = 0
  shelf['externalReferenceId'] = 'string'
  shelf['height'] = 0
  shelf['id'] = 0
  shelf['orientationY'] = 0
  shelf['orientationYaw'] = 0
  shelf['orientationZ'] = 0
  shelf['orientationx'] = 0
  shelf['positionX'] = 0
  shelf['positionY'] = 0
  shelf['positionZ'] = 0
  shelf['productGroupId'] = 0
  shelf['storeId'] = 0
  shelf['width'] = 0
  store_id = str(10)
  post_entity(shelf, 'Shelf', "http://ked.informatik.uni-bremen.de:8090/k4r-core/api/v0/stores/" + store_id + "/shelves")

def get_shelves(data):
  pass

def get_shelf_layers(data):
  pass

def post_data(data):
  shelves = get_shelves(data)
  store_id = 10 #for example
  post_entity(shelves, store_id)

if __name__ == "__main__":
  data = json.loads(open('data/ERP.json').read())
  post_data(data)