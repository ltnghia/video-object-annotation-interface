import json
from pprint import pprint

def color_palette():

    palette = []
    palette_dist = {}

    color = {}
    color['id'] = 1
    color['category'] = 'pedestrian'
    color['color'] = 'blue'
    color['rgb'] = [0, 0, 255]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 2
    color['category'] = 'rider'
    color['color'] = 'yellow'
    color['rgb'] = [255, 255, 0]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 3
    color['category'] = 'car'
    color['color'] = 'brown'
    color['rgb'] = [139, 69, 19]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 4
    color['category'] = 'truck'
    color['color'] = 'dark green'
    color['rgb'] = [0, 100, 0]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 5
    color['category'] = 'bus'
    color['color'] = 'red'
    color['rgb'] = [255, 0, 0]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 6
    color['category'] = 'motorcycle'
    color['color'] = 'deep pink'
    color['rgb'] = [255, 20, 145]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 7
    color['category'] = 'bicycle'
    color['color'] = 'orange'
    color['rgb'] = [255, 165, 0]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 8
    color['category'] = 'train'
    color['color'] = 'navy'
    color['rgb'] = [0, 0, 128]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 9
    color['category'] = 'traffic light'
    color['color'] = 'purple'
    color['rgb'] = [160, 32, 240]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    color = {}
    color['id'] = 10
    color['category'] = 'traffic sign'
    color['color'] = 'gray'
    color['rgb'] = [128, 128, 128]
    palette.append(color)
    palette_dist[color['id']] = color['rgb']

    outfile = open('./color_palette.json', 'w')
    x = json.dumps(palette)
    # pprint(x)
    outfile.write(x)
    outfile.close()

    return palette_dist