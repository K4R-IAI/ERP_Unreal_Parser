#!/usr/bin/env python

import csv
import json
import math
from geometry_msgs.msg import Pose
from shapely.geometry import Point, LineString
from shapely.geometry.polygon import Polygon
import tf

def calc_side_distance(point, line_a_b):
  if len(line_a_b) == 2:
    return abs(line_a_b[0] * point.x - point.y + line_a_b[1]) / math.sqrt(line_a_b[0] * line_a_b[0] + 1)
  else:
    return abs(line_a_b[0] - point.x)

class Product:
  def __init__(self, name):
    self.name = name
    self.items = []
    self.shelves = []
    self.locations = {}

  def calc_layers(self):
    for item in self.items:
      if item.shelf: #TODO: delete
        for i, layer in enumerate(item.shelf.layers):
          if layer.z_min <= item.height and item.height <= layer.z_max:
            item.layer = item.shelf.layers[i]
            if not item.shelf.id in self.locations:
              self.locations[item.shelf.id] = {}
            if not 'Layer ' + str(item.layer.num) in self.locations[item.shelf.id]:
              self.locations[item.shelf.id]['Layer ' + str(item.layer.num)] = {}

  def calc_facings(self):
    for item in self.items:
      if item.shelf: #TODO: delete
        side_distance = calc_side_distance(item.position, item.shelf.side_line_a_b)
        if not self in item.layer.orders:
          item.layer.orders[self] = [side_distance]
          self.locations[item.shelf.id]['Layer ' + str(item.layer.num)] = {}
          self.locations[item.shelf.id]['Layer ' + str(item.layer.num)]['Facing'] = 1
        else:
          same_facing = False
          for side_distance_in_one_shelf_layer in item.layer.orders[self]:
            if side_distance - side_distance_in_one_shelf_layer < 0.02 and side_distance - side_distance_in_one_shelf_layer > -0.02:
              same_facing = True
          if not same_facing:
            item.layer.orders[self].append(side_distance)
            self.locations[item.shelf.id]['Layer ' + str(item.layer.num)]['Facing'] += 1

  def __repr__(self):
    return str(self.name)

class Item:
  def __init__(self, data):
    self.name = str(data[0])
    self.position = Point(float(data[1]), float(data[2]))
    self.height = float(data[3])
    self.shelf = None
    self.layer = None
  def __repr__(self):
    return self.name + str(' at ') + str([self.position.x, self.position.y, self.height])

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
  def __init__(self, data, shelf_id, depth, width):
    self.id = shelf_id
    self.type = str(data[0])
    self.center = [float(data[1]), float(data[2])]
    self.depth = depth
    self.width = width
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

  def calc_orders(self):
    for layer in self.layers:
      for product in layer.orders:
        for order in layer.orders[product]:
          layer.orders_sorted.append((product, order))
      layer.orders_sorted.sort(key=lambda x: x[1])
      for i, order_sorted in enumerate(layer.orders_sorted):
        if 'Layer ' + str(layer.num) in order_sorted[0].locations[self.id]:
          order_sorted[0].locations[self.id]['Layer ' + str(layer.num)]['Order'] = i+1

  def __repr__(self):
    return str(self.id) + ' - ' + str(self.center) + ' - ' + self.type + ' - ' + str(self.polygon)

class Layer:
  def __init__(self, num, z_min, z_max):
    self.num = num
    self.z_min = z_min
    self.z_max = z_max
    self.orders = {}
    self.orders_sorted = []
  def __repr__(self):
    return 'Layer ' + str(self.num) + ' - ' + str([self.z_min, self.z_max])

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
  check_unlocated_products(products, shelves)

def check_unlocated_products(products, shelves, fix_unlocated=False):
  for product in products:
    for item in product.items:
      if not item.shelf:
        nearest_dist = float('inf')
        for shelf in shelves:
          if shelf.polygon.exterior.distance(item.position) < nearest_dist:
            nearest_dist = shelf.polygon.distance(item.position)
            nearest_shelf = shelf
        print('Item ' + str(item) + ' is unlocated, nearest shelf is ' + nearest_shelf.id + ' located at ' + str(nearest_shelf.center) + ', distance ' + str(nearest_dist))
        if fix_unlocated:
          print('Item ' + str(item) + ' will be located at shelf ' + nearest_shelf.id)
          item.shelf = nearest_shelf
          if not product in nearest_shelf.products:
            nearest_shelf.products.append(product)
          if not nearest_shelf in product.shelves:
            product.shelves.append(nearest_shelf)

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
    shelf_bottoms = []
    shelf_layers = []
    layer_heights = {}
    for data in csv_reader:
      if 'ShelfSystem' in str(data[0]):
        shelf_id += 1
        if 'H160T4L10W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.6, 1.0))
        if 'H160T6L10G' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 1.2, 1.0))
        if 'H200T7L10W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.85, 1.0))
        if 'H180T5L10W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.6, 1.0))
        if 'H200T5L6W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.6, 0.7))
        if 'H200T6L10W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.7, 1.0))
        if 'H200T6L12W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.7, 1.25))
        if 'H200T6L6W' in str(data[0]):
          shelves.append(Shelf(data, str('Shelf ') + str(shelf_id), 0.7, 0.65))
        layer_heights[shelves[-1]] = []
      elif 'Bottom' in str(data[0]):
        shelf_bottoms.append(data)
      elif 'ShelfLayer' in str(data[0]):
        shelf_layers.append(data)
    for data in shelf_bottoms:
      for shelf in shelves:
        if shelf.polygon.contains(Point(float(data[1]), float(data[2]))):
          layer_heights[shelf].append(float(data[3]))
    for shelf in shelves:
      if not layer_heights[shelf]:
        print('Shelf ' + shelf.type + ' does not have bottom layer, its bottom height will be set to 0.0')
        layer_heights[shelf].append(0.0)
    for data in shelf_layers:
      for shelf in shelves:
        if shelf.polygon.contains(Point(float(data[1]), float(data[2]))):
          layer_heights[shelf].append(float(data[3]))
    for shelf in layer_heights:
      layer_heights[shelf].sort()
      if len(layer_heights[shelf]) > 1:
        for i in range(len(layer_heights[shelf])-1):
          shelf.layers.append(Layer(i+1, layer_heights[shelf][i], layer_heights[shelf][i+1]))
        shelf.layers.append(Layer(i+2, layer_heights[shelf][i+1], float('inf')))
      else:
        shelf.layers.append(Layer(1, layer_heights[shelf][0], float('inf')))
    for shelf in shelves:
      print(shelf.id + ', type ' + shelf.type + ', located at ' + str(shelf.center) + ', width ' + str(shelf.width) + ', depth ' + str(shelf.depth) + ' is created')
  return shelves

def write_output(products):
  data = {}
  for product in products:
    for item in product.items:
      if not item.name in data:
        data[item.name] = {}
        data[item.name]['locations'] = product.locations
  with open('output/ERP.json', 'w') as outfile:
    json.dump(data, outfile, indent=2)

if __name__ == "__main__":
  products = csv_to_products('data/allitems.csv')
  shelves = csv_to_shelves('data/allshelves.csv')
  fill(products, shelves)
  for product in products:
    product.calc_layers()
    product.calc_facings()
  for shelf in shelves:
    shelf.calc_orders()
  write_output(products)