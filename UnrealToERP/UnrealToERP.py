#!/usr/bin/env python

import csv
from geometry_msgs.msg import Pose

class Product:
  def __init__(self, data):
    self.items = []
    self.shelf_owner = None
    self.layer = None
    self.facing = None
  def __repr__(self):
    return str(self.items)

class Item:
  def __init__(self, data):
    self.name = str(data[0])
    self.pose = Pose()
    self.pose.position.x = float(data[1])
    self.pose.position.y = float(data[2])
    self.pose.position.z = float(data[3])
    self.pose.orientation.x = float(data[4])
    self.pose.orientation.y = float(data[5])
    self.pose.orientation.z = float(data[6])
    self.pose.orientation.w = float(data[7])
  def __repr__(self):
    return self.name

def csv_to_products():
  with open("data/allitems.csv", mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    products = []
    for row in csv_reader:
      if not products:
        products.append(Product(row))
        products[0].items.append(Item(row))
  return products

if __name__ == "__main__":
  products = csv_to_products()
  print(products)
