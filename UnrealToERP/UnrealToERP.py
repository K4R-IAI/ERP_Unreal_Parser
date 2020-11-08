#!/usr/bin/env python

import csv
import json
from geometry_msgs.msg import Pose

class Product:
  def __init__(self, data):
    self.items = []
    self.items_front = []
    self.shelf_owner = None
    self.layers = []
    self.facing = 0

  def calc_items_front(self):
    for item in self.items:
      if self.items_front:
        if item.pose.position.x > self.items_front[-1].pose.position.x:
          self.items_front[-1] = item
        elif item.pose.position.x == self.items_front[-1].pose.position.x:
          self.items_front.append(item)
      else:
        self.items_front.append(item)

  def calc_facing(self):
    items_front_line = []
    max_facing = 0
    for i, item in enumerate(self.items):
      if items_front_line:
        if item.pose.position.z == items_front_line[-1].pose.position.z:
          items_front_line.append(item)
          if i == len(items_front_line) - 1:
            max_facing = len(items_front_line)
        else:
          if len(items_front_line) > max_facing:
            max_facing = len(items_front_line)
          items_front_line = [item]
      else:
        items_front_line.append(item)
    self.facing = max_facing

  def calc_layer(self, shelf):
    for item in self.items:
      for i, layer in enumerate(shelf.layers):
        if layer.z_min <= item.pose.position.z and item.pose.position.z <= layer.z_max:
          if not i in self.layers:
            self.layers.append(i)

  def __repr__(self):
    return str(self.items[0]) + ' - ' + str(len(self.items)) + ' items - ' + str(len(self.layers))  + ' layers (' + str(self.layers) + ')'

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

class Shelf:
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
    self.layers = []
  def __repr__(self):
    return str(self.name) + ': ' + str(self.layers)

class Layer:
  def __init__(self, z_min, z_max):
    self.z_min = z_min
    self.z_max = z_max
  def __repr__(self):
    return str(self.z_min) + ' - ' + str(self.z_max)

def csv_to_products():
  with open("data/products.csv", mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    next(csv_reader)
    first_row = next(csv_reader)
    products = []
    products.append(Product(first_row))
    products[0].items.append(Item(first_row))
    for data in csv_reader:
      item = Item(data)
      if products[-1].items[-1].name != item.name:
        products.append(Product(data))
      products[-1].items.append(item)
  return products

def csv_to_shelves():
  with open("data/shelves.csv", mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    next(csv_reader)
    shelves = []
    z_min = 0
    for data in csv_reader:
      if 'ShelfSystem' in str(data[0]):
        if z_min > 0:
          shelves[-1].layers.append(Layer(z_min, float('inf')))
        shelves.append(Shelf(data))
      elif 'Bottom' in str(data[0]):
        z_min = float(data[3])
      elif 'Tiles' in str(data[0]):
        shelves[-1].layers.append(Layer(z_min, float(data[3])))
        z_min = float(data[3])
    shelves[-1].layers.append(Layer(z_min, float('inf')))
  return shelves

def write_output(products):
  data = {}
  for product in products:
    for item in product.items:
      if not item.name in data:
        data[item.name] = {}
        data[item.name]['layers'] = product.layers
        data[item.name]['facing'] = product.facing
  with open('output/ERP.json', 'w') as outfile:
    json.dump(data, outfile)

if __name__ == "__main__":
  products = csv_to_products()
  shelves = csv_to_shelves()
  for product in products:
    product.calc_facing()
    product.calc_layer(shelves[0])
  print(products)
  write_output(products)