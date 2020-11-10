#!/usr/bin/env python

import csv
import json
import math
from geometry_msgs.msg import Pose
from shapely.geometry import Point, LineString
from shapely.geometry.polygon import Polygon
import tf

def calc_dist_point_to_line(point, line_a_b):
  if len(line_a_b) == 2:
    return abs(line_a_b[0] * point.x - point.y + line_a_b[1]) / math.sqrt(line_a_b[0] * line_a_b[0] + 1)
  else:
    return abs(line_a_b[0] - point.x)

class Product:
  def __init__(self, name):
    self.name = name
    self.items = []
    self.shelves = []
    self.layers = {}
    self.facings = {}

  def calc_facings(self):
    dist_to_sides = {}
    for item in self.items:
      if item.shelf: #TODO: delete
        dist_to_side = calc_dist_point_to_line(item.position, item.shelf.side_line_a_b)
        if not item.shelf.id in dist_to_sides:
          dist_to_sides[item.shelf.id] = [dist_to_side]
          self.facings[item.shelf.id] = 1
        else:
          same_facing = False
          for dist in dist_to_sides[item.shelf.id]:
            if dist_to_side - dist < 0.01 and dist_to_side - dist > -0.01:
              same_facing = True
              break
          if not same_facing:
            dist_to_sides[item.shelf.id].append(dist_to_side)
            self.facings[item.shelf.id] += 1

  def calc_layers(self):
    for item in self.items:
      if item.shelf: #TODO: delete
        for i, layer in enumerate(item.shelf.layers):
          i+=1
          if layer.z_min <= item.height and item.height <= layer.z_max:
            if not item.shelf.id in self.layers:
              self.layers[item.shelf.id] = [i]
            else:
              if not i in self.layers[item.shelf.id]:
                self.layers[item.shelf.id].append(i)

  # def calc_layer(self, shelf):
  #   for item in self.items:
  #     for i, layer in enumerate(shelf.layers):
  #       if layer.z_min <= item.pose.position.z and item.pose.position.z <= layer.z_max:
  #         if not i in self.layers:
  #           self.layers.append(i)

  def __repr__(self):
    return str(self.name)

class Item:
  def __init__(self, data):
    self.name = str(data[0])
    self.position = Point(float(data[1]), float(data[2]))
    self.height = float(data[3])
    self.shelf = None
  def __repr__(self):
    return self.name

def transform2d(x_trans, y_trans, x_rot, y_rot, yaw):
  c = math.cos(yaw)
  s = math.sin(yaw)
  x_res = x_rot * c + y_rot * s + x_trans
  y_res = -x_rot * s + y_rot * c + y_trans
  return (x_res, y_res)

def calc_a_b(x1, x2, y1, y2):
  if not x2 == x1:
    a = (y2 - y1)/(x2 - x1)
    b = y1 - x1 * a
    return [a, b]
  else:
    return [x1]

class Shelf:
  def __init__(self, data, shelf_id):
    self.id = shelf_id
    self.type = str(data[0])
    self.depth = 0.8
    self.width = 1.0
    self.polygon = self.set_polygon(data)
    self.layers = []
    self.products = []

  def set_polygon(self, data):
    quaternion = (float(data[4]), float(data[5]), float(data[6]), float(data[7]))
    euler = tf.transformations.euler_from_quaternion(quaternion)
    yaw = euler[0]
    p1 = transform2d(float(data[1]), float(data[2]), -self.width/2, -self.depth/2, yaw)
    p2 = transform2d(float(data[1]), float(data[2]), self.width/2, -self.depth/2, yaw)
    p3 = transform2d(float(data[1]), float(data[2]), self.width/2, self.depth/2, yaw)   
    p4 = transform2d(float(data[1]), float(data[2]), -self.width/2, self.depth/2, yaw)
    self.side_line_a_b = calc_a_b(p2[0], p3[0], p2[1], p3[1])
    return Polygon([p1, p2, p3, p4])
  def __repr__(self):
    return str(self.id) + ' - ' + self.type + ' - ' + str(self.polygon)

class Layer:
  def __init__(self, z_min, z_max):
    self.z_min = z_min
    self.z_max = z_max
  def __repr__(self):
    return str(self.z_min) + ' - ' + str(self.z_max)

def fill(products, shelves):
  for product in products:
    for shelf in shelves:
      for item in product.items:
        if shelf.polygon.contains(item.position):
          item.shelf = shelf
          if not product in shelf.products:
            shelf.products.append(product)
          if not shelf in product.shelves:
            product.shelves.append(shelf)
      
def csv_to_products(csv_items):
  with open(csv_items, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    first_row = next(csv_reader)
    products = []
    products.append(Product(str(first_row[0])))
    products[0].items.append(Item(first_row))
    for data in csv_reader:
      item = Item(data)
      if products[-1].name != str(data[0]):
        products.append(Product(str(data[0])))
      products[-1].items.append(item)
  return products

def csv_to_shelves(csv_shelves):
  with open(csv_shelves, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    shelves = []
    shelf_id = 0
    shelf_layers = []
    layer_heights = {}
    for data in csv_reader:
      if 'ShelfSystemH200T7L10W' in str(data[0]):
        shelves.append(Shelf(data, str(shelf_id)))
        layer_heights[shelves[-1]] = []
        shelf_id += 1
      elif 'ShelfLayer' in str(data[0]):
        shelf_layers.append(data)
    for data in shelf_layers:
      for shelf in shelves:
        if shelf.polygon.contains(Point(float(data[1]), float(data[2]))):
          layer_heights[shelf].append(float(data[3]))
    for shelf in layer_heights:
      layer_heights[shelf].sort()
      for i in range(len(layer_heights[shelf])-1):
        shelf.layers.append(Layer(layer_heights[shelf][i], layer_heights[shelf][i+1]))
      shelf.layers.append(Layer(layer_heights[shelf][i+1], float('inf')))
  return shelves

def write_output(products):
  data = {}
  for product in products:
    for item in product.items:
      if not item.name in data:
        data[item.name] = {}
        data[item.name]['layers'] = product.layers
        data[item.name]['facings'] = product.facings
  with open('output/ERP.json', 'w') as outfile:
    json.dump(data, outfile)

if __name__ == "__main__":
  products = csv_to_products('data/allitems.csv')
  #print(products)
  shelves = csv_to_shelves('data/allshelves.csv')
  #print(shelves)
  fill(products, shelves)

  products_valid = []
  for product in products:
    if product.shelves:
      products_valid.append(product)
      products = products_valid

  for product in products:
    product.calc_facings()
    product.calc_layers()
  #   for shelf in shelves:
  #     product.calc_layer(shelves[0])

  #print(products)
  write_output(products)