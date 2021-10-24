#!/usr/bin/env python
# coding: utf-8

# # Vérifier Pipettage Salive

# Le but de ce script est de montrer commnent utiliser une fonction pour vérifier le bon pipettage d'une série d'échantillons difficiles à prélever (par exemple des écchantillons visqueux ou en faible volume). La démonstration est réalisée dans des pots à urines, censés contenir de la salive. 
# * v 0.1 : début : Vérification élémentaires et évoluée.
# * v 0.2 : mofif du pythonpath pour que le script fonctionne depuis son répertoire. Ajout d'une possibilité d'annuler la vérification pour la suite des échantillons.
# * v 0.3 : relecture.
# * v 0.4 : création d'une démonstration. Elimination des codes inutiles pour la démonstration.
# Je retravaille sur ce code à la maison en oct 2021. 

# In[1]:


import opentrons

from opentrons.types import Point
from opentrons import protocol_api
import os
import json


# # To use Jupyter-notebook, we add theses lines

# In[2]:


import opentrons.execute
from opentrons import protocol_api
from opentrons import simulate


# In[3]:


os.sys.path.insert(1, os.path.realpath("../my_lib/"))
os.path
from ot_2_functions import *


# # Direct access to OT-2 or simulation ?

# In[4]:


# simulation : 
#     True : an OT-2 is physically connected.
#     False : an OT-2 in not physically connected. 
simulation = True 


# # Improve the protocol class
# 
# In a non simulation mode, you can see a result using `ctx.comment()` function. 
# 
# In simulation mode, we add a methode to ctx (an instance of the opentrons.protocol_api.protocol_context.ProtocolContext class). You can do it as following : 

# In[5]:


def print_simulation_result(self,):
    for line in self.commands():
        print(line)
        
if simulation: 
    ctx = simulate.get_protocol_api('2.9')
    # Redéfinir la fonction comment() et la fonction messages de 
    # opentrons.protocol_api.protocol_context.ProtocolContext
    ctx.comment = print
    opentrons.protocol_api.protocol_context.ProtocolContext.messages = print_simulation_result 
else:
    ctx = opentrons.execute.get_protocol_api('2.9')


# Now, you can use :  (NE FONCTIONNE PAS !)

# In[6]:


ctx.comment("This is an example of comment") 


# # Starting to move OT-2

# In[7]:


# metadata
metadata = {
    'protocolName': 'S2 Station A Kingfisher Version 2',
    'author': 'Eva González & José Luis Villanueva (jlvillanueva@clinic.cat)',
    'source': 'Hospital Clínic Barcelona',
    'apiLevel': '2.9',  # Original 2.0
    'description': 'Protocol for Kingfisher sample setup (A) - Viral/Pathogen II Kit (ref A48383)'
}

'''
'technician': '$technician',
'date': '$date'
'''


# In[8]:


ctx.home()


# # Load labware and modules

# ##  Load sample racks

# ## Importing sandard and custom labware in Jupyter notebook
# 

# In[9]:


##################################
# Load tip_racks
tips1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000 µl filter tiprack')
            for slot in ['10']]  # Replace by [7, 10, 11] for example for other tipracks.


# In[ ]:





# # Ajout d'un portoir pour les urines ou les salives

# In[10]:


# portoir_6_urines.json
with open("../my_labware/portoir_6_urines.json") as my_6_urine_vials_rack_file:
    six_urines_rack_ref = json.load(my_6_urine_vials_rack_file)

urines_rack = ctx.load_labware_from_definition(six_urines_rack_ref, 11, 'Urines/Salives' )


# # Deck summary

# In[11]:


deck_summary(ctx)


# # Load pipettes

# In[12]:


p1000 = ctx.load_instrument('p1000_single_gen2', 'left', tip_racks=tips1000)  # load P1000 pipette


# # Pipette in urines vials for saliva

# ## Pipette virtuelle pour mise au point plus rapide

# In[13]:


class VirtualPipette:
    def __init__(self):
        pass
    def aspirate(self, a,b,  *kwwarks):
        print("aspiration")
    def dispense(self, a, b,  *kwargs):
        print("dispense")
    def move_to(self, a, *kwargs):
        print("move")
    def blow_out(self, *key):
        print("Souffle")


# In[24]:


from enum import IntEnum

class Status(IntEnum):
    tryed = 0
    retesting = 1
    confirmed = 2
    confirmed_after_new_action = 3 # 
    confirmed_then_auto_confirmed = 4 # confirmer l'échantillon et confirmer tout le reste automatiquement. 
    rejected = 5
    
class ControlledObject:
    """Une classe pour vérifier le pipettage"""
    def __init__(self, pipette, source_loc, dest_loc, z_up = 20):
        self.pipette = pipette
        self.vol = 300
        self.source_loc = source_loc
        self.dest_loc = dest_loc
        self.z_up = z_up
        
    def do(self):
        print("     Aspiration dans le puits ",self.source_loc.labware)
        self.pipette.aspirate(self.vol, self.source_loc)
        self.pipette.move_to(self.source_loc.move(Point(0,0,self.z_up)))
        
    def undo(self):
        print("     Rejet de ", self.source_loc.labware)
        self.pipette.dispense(self.vol, self.source_loc)
        self.pipette.move_to(self.source_loc)
        
    def done(self):
        print("     Transfert dans", self.dest_loc.labware)
        self.pipette.dispense(self.vol, self.dest_loc)
        self.pipette.blow_out()


# In[15]:


def controlled_action(item, ctrled_object, verify = True):
    
    print(f"Traitement de l'échantillon {item}")

    ctrled_object.do()

    if verify:
        status = Status.tryed
        
        while True:  
    #     while status not in [Status.confirmed, Status.confirmed_after_new_action, Status.rejected]:
            if status == Status.retesting:
                ctrled_object.undo()
                ctrled_object.do()

            rep = input(f"""     L'action est-elle correcte ? 
               O ou Enter : OK ;     R : Réessayer ; 
               X : Accepter cet échantillon et tous les autres ;
               A : Annuler échantillon {item} ? : """).upper()
            if len(rep):
                rep = rep[0]

            if rep == "" or rep == "O":
                if status == Status.tryed:
                    status = Status.confirmed
                elif status == Status.retesting:
                    status = Status.confirmed_after_new_action
                print(f"     cas {item} a été confirmé")
                break

            elif rep == "R":
                print(f"     cas {item} non confirmé, nous allons essayer de le reprendre")           
                status = Status.retesting

            elif rep == "A":
                status = Status.rejected
                print(f"     cas {item} est annulé (Rejecté)")
                break

            elif rep == "X":
                status = Status.confirmed_then_auto_confirmed
                print(f"     cas {item} a été confirmé.\nConfirmation automatique activée.")
                break

        if status in[ Status.confirmed, 
                      Status.confirmed_after_new_action, 
                      Status.confirmed_then_auto_confirmed ]:
            pipette.done()
        elif status == Status.rejected:
            pipette.undo()
    else: # Pas de verification
        status = Status.confirmed
        pipette.done()
    return status


# In[16]:


VIRTUAL = True


# # RUN 1

# In[17]:


if VIRTUAL:
    la_pipette = VirtualPipette()
else: 
    la_pipette = p1000
    if p1000.hw_pipette['has_tip']:    
        p1000.drop_tip()
    p1000.pick_up_tip()

worklist = []

verify = True
for well in urines_rack.wells()[:3]:
    pipette = ControlledObject(la_pipette, 
                               source_loc = well.bottom(3), 
                               dest_loc= urines_rack.wells()[5].bottom(6),
                               z_up = 60
                              )
    res_status = controlled_action(well, pipette, verify = verify)
    worklist.append((well, res_status))
    if res_status == Status.confirmed_then_auto_confirmed:
        verify = False

if not VIRTUAL : 
    p1000.drop_tip()
    
print("Résumé")
for (ech, status) in worklist:  
    print(ech, status)


# # Run 2
# Un minirun, pour gérer précisément le pipettage. 

# In[20]:


# Un pipettage très précis


# In[22]:


p1000.pick_up_tip()


# In[23]:


p1000.aspirate(200, urines_rack.well('A1'))
p1000.air_gap(50, height=-15)
p1000.dispense(250, urines_rack.well('A1').top(-10))
p1000.blow_out()
p1000.touch_tip(urines_rack.well('A1'), radius=0.5, v_offset= 30)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[19]:



opentrons.execute.get_protocol_api('2.9')


# In[ ]:


bi

