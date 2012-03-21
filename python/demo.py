#dreamingforward@gmail.com
#pangaia.sf.net

"""
A very crude demo giving a feel for the 3-d environment potential for a content-centric web.
Rotate view with the right-mouse drag and Zoom using both buttons (Mac: use Option key).
"""

#TODO:
#1) Create a node class derived from sphere object.
#2) Add ability to Label a node.
#3) Add ability to Link/associate nodes.  Animate linking with some [[gravity model]], function of node mass, etc.
#4) Add ability to select a number of nodes and Group them.
#5) Currently drawing random nodes.  Create an interface to import gmail messages and prompt user to sort.
#6) since vpython has no depth shading, use built-in camera w/eye tracking to move the scene around as head moves.

#set a fixed light at the top, and make a frame that will rotate objects without affecting the light.
#consider the vpython4 attenuation attribute of a light source and consider that it is a factor of the scaling relationship between the light source and the objects.
#Also, using the built-in camera with eye-tracking for depth discernment (idea from Geoff Chesshire)

from __future__ import division   #XXX: shouldn't have to do this -- isn't it the future already?

from visual import *  #this pulls in the visual python library from the VPython
from random import *  #from the Python standard library
from graph import *   #pangaia module

###Rule of Thumb #1:  Put the most arbitrary values at the top of the code.  Let users tweak.
num_nodes = 100                   #number of nodes to draw
p_nodes_lit = 0.07                  #light 7% of the nodes, chosen randomly

###Rule of Thumb #2:  Variable casing should be dynamic -- if variable is a part of a larger whole, use lower_case, otherwise CamelCase.
UserNodeName = "Neophyte"  #This will be your personal Node name as seen from the view of the social garden
default_name = "node"      #Nodes will take this name plus a number

###Visual-python constants
scene.title = UserNodeName or raw_input("Name:") #prompt for user's name if not registered, "think for the future: what name do you want to be addressed as in eternity?"
scene.width, scene.height = 1440, 900  #XXX change this to fit your screen, pixels.
scene.ambient = color.gray(0.05)   #sets background light:  should be a function of how many viewers rather than arbitrary
#scene.lights=[ ]                  #eliminates default lights
#scene.lights=local_light(pos=(0,0,0), color=color.white, local=True, attentuation=(1,1,5))
#scene.lights=[distant_light(direction=(0, 1, 0), color=color.white, attentuation=(1,1,10))] #(1,1,0.8))]
scene.material = materials.diffuse #sets default material when none specified
#scene.stereo="redcyan"            #gives nice depth effect if you have red/cyan glasses, ultimately plan is to use built-in camera if availble

mean_node_radius = 20           #This should start 0 or 1 and is akin to mass.
world_radius =  int(mean_node_radius*num_nodes/8)    #XXX this isn't the right equation   #this sets the default "size" of the world, a cubic, cartesian volume determined by the number of nodes.  All vector ops reference this coordinate space. A function of num_nodes, as radius=1 places a known lower bound. VPython caluculates a "bounded box" that will contain everything in the scene.
base_color = color.green           #nodes start in the middle of the rainbow
base_opacity = 0.95                #A function of how much trust there is in the network.  Lower values ==> greater trust

##The view in the blank window will depend on whether you're in your own Node (the "polar coordinate view) or viewing from outside it (the "cartesian veiw").
##Inside your node, you are seeing all the relationships that pertain to you, organized around your central basis (i.e. machine name)
##Outside your node, you navigate the (relatively unrelated) universe of nodes.
##Perhaps could zoom to edge of node-field and then (*bleep*) transit out to see the universe.


## Should encapsulate these into a class, integrated with graph nodes.
#class node(sphere):
#    def __init__(self, pos, mass, valence, lit, noosphere, **kwargs):
#        super().__init__(**kwargs)
#        try:
#            radius=kwargs["radius"]
#            radius=max(1,radius-thickness)
#        except KeyError:
#            pass
#        kwargs["radius"]=radius
#        sphere(kwargs) #draw a second sphere


def rand3tuple(start = -world_radius, stop = world_radius):
    """"Return a 3-tuple  consiting of random integers between start and stop."""
    return (randint(start, stop), randint(start, stop), randint(start, stop*2)) #note adjustment on z 


def atmos(valence, ambient=scene.ambient):   #XXX sloppy
    """Returns the color of the outershell, given node color and ambient background."""
    c = vector(color.rgb_to_hsv(vector(valence)*0.5))  #first reduce all color values
    #c[1] *= 0.5 #then, reduce saturation towards the background XXX:currently assuming ambient=gray of some kind
    c=vector(color.hsv_to_rgb(c))
    c[2] = min(c[2] + 0.2, 1)  #XXX this is totally arbitrary, but I like a little blue in there.  Ideally should move towards the ambient background color.
    return c

##def world_to_pixels(z):
##    """Adjust size for depth."""
##    return 1 + (world_radius * 2) / 20

#This looks nice: inner sphere: chrome, light.color=green, outsphere=glass, opacity=0.4
#Also, inner sphere: glass, color=gray, opacity=0.5, outsphere, glass, color=green, opacity=0.3
#Note: materials = {wood, rough, marble, plastic, earth, diffuse, emissive, unshaded, shiny, chrome, blazed, silver, BlueMarbe, bricks}
def node(name, pos, mass=mean_node_radius, valence=base_color, lit=False, noosphere=mean_node_radius/2, **kwargs):  #noosphere argument arbitrary
    """Draws a node on the screen.  Currently, a node is a sphere, plus an atmosphere."""
    label(pos=pos, text=name, box=False, opacity=0, color=color.gray(0.4), line=False, height=6)
    hsvcolor = vector(color.rgb_to_hsv(valence))
    if lit:  #primitve activity model:  make it a light source  #local_light(pos=pos, color=(1.0,0,0)) or at least maximize saturation #XXX is this working?
        local_light(pos=pos, color=color.white)
        hsvcolor[1] = 1 #maximize saturation at least.
    else:
        hsvcolor[2] *= 0.3 #reducing lightness
    valence = color.hsv_to_rgb(hsvcolor)
    sphere(pos=pos, color=valence, opacity=base_opacity, radius=mass, material=materials.emissive if lit else scene.material, **kwargs) #inner sphere  (Note: try material=chrome)
    sphere(pos=pos, color=atmos(valence), opacity=0.2*base_opacity, radius=mass+noosphere, material=materials.emissive, **kwargs) #outer sphere, color should be converted to hsv and value amplified assuming ambient color is shade of pure white

###################################################################

g = Graph()

### Rotation should be tried...
##for i in arange(0,pi):
##    f.axis=(0,i,0)

##Depth-cueing experiment #2: simply place semi-tranparent, scene.ambient-colored boxes from front to back.  They'll get progressively darker away from the user.
#for i in range(10000): #-world_radius, +world_radius*2, int(world_radius/1)):
#    sphere(pos=rand3tuple(), material=materials.emissive, opacity=0.02*base_opacity, color=color.gray(0.2), radius=mean_node_radius)


##cities={"Denver","Seattle","Portland","Boise","Fargo","LosAngeles"}
##The actual drawing of nodes here
for i in range(num_nodes):
    light = (random() > 1 - p_nodes_lit)
    name = default_name + str(i)
    
    if light:
        print "lit", name
        
    g.add(name)  #this really doesn't do anything right now
    node(name, rand3tuple(), randint(1,mean_node_radius), base_color, light, randint(int(mean_node_radius/2), mean_node_radius*2))


### Experiment in edge drawing
##nodes = scene.objects[:]
##for s in nodes:
##    tail=choice(nodes) #pick a random destination node
##    #cylinder(pos=s.pos, axis=tail.pos, radius=10, color=(0.2,0.2,0.1))
##    curve(pos=[s.pos, tail.pos], color=(0.1,0.1,0.1), radius=4, visible=False)

## Simple event handling, currently only can click nodes and affect radius
while True:
    rate(100)  #sets an upper-bound on how often (per second) the loop runs.
    #f=scene.forward
    #print(scene.forward)
    if scene.mouse.events:
        mm=scene.mouse.getevent()
        if mm.pick==None: #create new sphere
            node("light", pos=mm.pos, lit=True)
        else:
            print mm.pick, mm.pick.radius
            if mm.shift:  #XXX this is crude need to send this to node object so it both spheres get adjusted
                mm.pick.radius -= 1
            else:
                mm.pick.radius += 1
    if scene.kb.keys:
        key=scene.kb.getkey()
        if key=="q":
            break
        #elif key == "Left-Shift"

print(g)
