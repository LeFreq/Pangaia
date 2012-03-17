#dreamingforward@gmail.com
#pangaia.sf.net

"""
A very crude demo giving a feel for the 3-d environment potential for a content-centric web.
Rotate view with the right-mouse drag and Zoom using both buttons (Mac: use Option key).
"""

#TODO:
#1) Add ability to Label a node.
#2) Add ability to Link/associate nodes.  Animate linking with some [[gravity model]], function of node mass, etc.
#3) Add ability to select a number of nodes and Group them.
#4) Currently drawing random nodes.  Create an interface to import gmail messages and prompt user to sort.
#5) since vpython has no depth shading, use built-in camera w/eye tracking to move the scene around as head moves.

#set a fixed light a t the top, and make a frame that will rotate objects without affecting the light.
#consider the vpython4 attenuation attribute of a light source and consider that it is a factor of the scaling relationship between the light source and the objects.
#Also, using the built-in camera with eye-tracking for depth discernment (courtesy Geoff Chesshire)

from __future__ import division   #XXX: should have to do this -- isn't it the future already?

from visual import *  #this is pulls in the visual python library
from random import *
from graph import *

UserNodeName = "Neophyte" #This will be your personal Node name as seen from the view of the social garden

scene.title = UserNodeName or raw_input("Name:") #prompt for user's name if not registered, "think for the future: what name do you want to be addressed as in eternity?"
scene.width, scene.height = 1440, 900  #XXX change this to fit your screen.
#scene.lights=[ ]                  ##eliminate default lights
#scene.lights=local_light(pos=(0,0,0), color=color.white, local=True, attentuation=(1,1,5))
scene.lights=[distant_light(direction=(0, 1, 0), color=color.green, attentuation=(1,1,10))] #(1,1,0.8))]
scene.material=materials.emissive  #sets default material when none specifid
scene.ambient=color.gray(0.05)     #sets background light
#scene.stereo="redcyan"            #gives nice depth effect if you have red/cyan glasses, ultimately should use built-in camera if availble


world_radius = 50000               #this sets the default "size" of the world (as a starting point) as a reference for all vector ops.
base_color = (0,0.7,0)              #nodes start green
base_opacity = 0.95               #0.05
default_mass = world_radius / 20  #specifies ratio of node radius to world radius

num_nodes= 100                    #number of spheres to draw

##The view in the blank window will depend on whether you're in your own Node (the "polar coordinate view) or viewing from outside it (the "cartesian veiw").
##Inside your node, you are seeing all the relationships that pertain to you, organized around your central basis (i.e. machine name)
##Outside your node, you navigate the (relatively unrelated) universe of nodes.
##Perhaps could zoom to edge of node-field and then (*bleep*) transit out to see the universe.


## Should encapsulate these into a class, integrated with graph nodes.
#class mysphere(sphere):
#    def __init__(self, thickness=5, **kwargs):
#        super().__init__(**kwargs)
#        try:
#            radius=kwargs["radius"]
#            radius=max(1,radius-thickness)
#        except KeyError:
#            pass
#        kwargs["radius"]=radius
#        sphere(kwargs) #draw a second sphere


def rand3tuple(start= -world_radius, stop = world_radius):
    """"Return a 3-tuple  consiting of random integers between start and stop."""
    return (randint(start, stop), randint(start, stop), randint(start, stop*2)) #note adjustment on z 


#This looks nice: inner sphere: chrome, light.color=green, outsphere=glass, opacity=0.4
#Also, inner sphere: glass, color=gray, opacity=0.5, outsphere, glass, color=green, opacity=0.3
#Note: materials = {wood, rough, marble, plastic, earth, diffuse, emissive, unshaded, shiny, chrome, blazed, silver, BlueMarbe, bricks}

# Function for standardizing sphere drawing
def node(pos, mass=default_mass, noosphere=default_mass/2, lit=False, **kwargs):
    """Draws a node on the screen."""
    if lit:  #XXX is this working?
        local_light(pos=pos, color=(1.0,0,0)) #XXX test color
    sphere(pos=pos, color=base_color, radius=mass, **kwargs) #inner sphere  (material=chrome looks pretty cool)
    sphere(pos=pos, color=(0,1,0.5), opacity=0.1*base_opacity, radius=mass+noosphere, material=materials.emissive, **kwargs) #outer sphere

###################################################################

### Rotation should be tried...
##for i in arange(0,pi):
##    f.axis=(0,i,0)

##Experiment with crude fog (takes a few moments to load up a million points)
##l=[]
##for i in range(1000000):
##    l.append(rand3tuple())    
##points(pos=l, size=1, color=color.gray(scene.ambient), size_units="world")

## The actual drawing of spheres here
#local_light(pos=(0,0,0))
for i in range(num_nodes):
    light = (randint(1,50) == 10)  #True 2% of the time
    if light: print "lit"
    node(pos=rand3tuple(), lit=light, mass=randint(1,0.1*world_radius))

### Experiment in edge drawing
##nodes = scene.objects[:]
##for s in nodes:
##    tail=choice(nodes) #pick a random destination node
##    #cylinder(pos=s.pos, axis=tail.pos, radius=10, color=(0.2,0.2,0.1))
##    curve(pos=[s.pos, tail.pos], color=(0.1,0.1,0.1), radius=4, visible=False)

## Simple event handling, currently only can click nodes and affect radius
while True:
    rate(100)
    #f=scene.forward
    #print(scene.forward)
    if scene.mouse.events:
        mm=scene.mouse.getevent()
        if mm.pick==None: #create new sphere
            node(pos=mm.pos, radius=100)
        else:
            print mm.pick, mm.pick.radius
            if mm.shift:
                mm.pick.radius+=1
            else:
                mm.pick.radius-=1
##    if scene.kb.keys:
##        key=scene.kb.getkey()
##        print key
##        #if key == "Left-Shift"

#cities={"Denver","Seattle","Portland","Boise","Fargo","LosAngeles"}
#g=Graph()
#print(g)
