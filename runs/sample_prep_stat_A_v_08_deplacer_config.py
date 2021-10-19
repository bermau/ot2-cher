#!/usr/bin/env python
# coding: utf-8

# Saple_prep_A
import math
import opentrons
from opentrons.types import Point
from opentrons import protocol_api
import os
from timeit import default_timer as timer
import json
from datetime import datetime

os.sys.path.insert(1, os.path.realpath("../my_lib/"))
import ot_2_functions as ot2lib

# metadata
metadata = {
    'protocolName': 'Tools for OT-2',
    'author': 'Bertrand Maubert',
    'source': 'Laboratoire du Centre hospitalier Emile Roux- Le Puy en Velay',
    'apiLevel': '2.9',  # Original 2.0
    'description': """Tools for OT-2 and Protocol for Kingfisher sample setup (A). 
    Protocol for Kingfisher sample setup (A) - Viral/Pathogen II Kit (ref A48383) 
    Adapted from covid19clinic project"""
}

# # Load labware and modules
import config_A as cf

ot2lib.deck_summary(cf.ctx)

cf.ctx.home()
# # Part from COVID19 projet
# Define the STEPS of the protocol
STEP = 0
STEPS = {  # Dictionary with STEP activation, description, and times
    1: {'Execute': True, 'description': 'Add samples (200 ul)'},
}

for s in STEPS:  # Create an empty wait_time
    if 'wait_time' not in STEPS[s]:
        STEPS[s]['wait_time'] = 0

    # Creating a log file
if not cf.ctx.is_simulating():
    print("ctx is a real OT-2")
    # Folder and file_path for log time
    logs_dir = '/var/lib/jupyter/notebooks/logs'
    logfile_path = logs_dir + '/KA_SampleSetup_viral_path2_time_log.txt'
    if not os.path.isdir(logs_dir):
        os.mkdir(folder_path)
    if not os.path.exists(logfile_path):
        print("Log file will be", logfile_path)
else:
    print("ctx is a simulation : no log")

samples = ot2lib.ReagentInLabware(name='Samples',
                                  flow_rate_aspirate=1,
                                  flow_rate_dispense=1,
                                  rinse=False,
                                  delay=0,
                                  reagent_reservoir_volume=700 * 24,
                                  num_wells=24,  # num_cols comes from available columns
                                  h_cono=4,
                                  v_fondo=4 * math.pi * 4 ** 3 / 3
                                  )  # Sphere

samples.vol_well = 700

def move_vol_multichannel(ctx, pipet, reagent, source, dest, vol, air_gap_vol, x_offset,
                          pickup_height, rinse, disp_height, blow_out, touch_tip, verbose=False, blow_out_offset=-5,
                          confirm_aspiration=False):
    '''
    x_offset: list with two values. x_offset in source and x_offset in destination i.e. [-1,1]
    pickup_height: height from bottom where volume
    rinse: if True it will do 2 rounds of aspirate and dispense before the tranfer
    disp_height: dispense height; by default it's close to the top (z=-2), but in case it is needed it can be lowered
    blow_out, touch_tip: if True they will be done after dispensing
    '''

    def help(msg):
        if verbose:
            input(msg)

    # Rinse before aspirating
    if rinse == True:
        custom_mix(ctx, pipet, reagent, location=source, vol=vol,
                   rounds=2, blow_out=True, mix_height=0,
                   x_offset=x_offset, blow_out_offset=-10)
    # SOURCE
    s = source.bottom(pickup_height).move(Point(x=x_offset[0]))
    help("after rinse ... suite")

    pipet.aspirate(vol, s, rate=reagent.flow_rate_aspirate)  # aspirate liquid

    help("after aspirate ... suite")

    if air_gap_vol != 0:  # If there is air_gap_vol, switch pipette to slow speed
        pipet.aspirate(air_gap_vol, source.top(z=-3),
                       rate=reagent.flow_rate_aspirate)  # air gap
    help("after air_gap ....continuer")

    if confirm_aspiration:
        rep = input("Aspiration correcte ? ENTER pour OK; Autre touche pour Non")
        if rep:
            print("Aspiration notée incorrecte pour puits, ", input_well.well_name)
        else:
            print("Ok , ", input_well)
    # GO TO DESTINATION
    drop = dest.top(z=disp_height).move(Point(x=x_offset[1]))

    print(drop)
    help("after drop : continuer");

    pipet.dispense(vol + air_gap_vol, drop,
                   rate=reagent.flow_rate_dispense)  # dispense all
    help("after dispense.... continuer")
    ctx.delay(seconds=reagent.delay)  # pause for x seconds depending on reagent

    if blow_out == True:
        pipet.blow_out(dest.top(z=blow_out_offset))
        help("End of blow_out")

    if touch_tip == True:
        pipet.touch_tip(radius=0.9, speed=20, v_offset=-5)
        help("End of touch tip")


def custom_mix(ctx, pipet, reagent, location, vol, rounds, blow_out, mix_height,
               x_offset, source_height=3, blow_out_offset=-5):
    '''
    Function for mixing a given [vol] in the same [location] a x number of [rounds].
    blow_out: Blow out optional [True, False]
    x_offset = [source, destination]
    source_height: height from bottom to aspirate
    mix_height: height from bottom to dispense
    '''
    if mix_height == 0:
        mix_height = 3
    pipet.aspirate(1,
                   location=location.bottom(z=source_height).move(Point(x=x_offset[0])),
                   rate=reagent.flow_rate_aspirate)
    for _ in range(rounds):
        pipet.aspirate(vol,
                       location=location.bottom(z=source_height).move(Point(x=x_offset[0])),
                       rate=reagent.flow_rate_aspirate)

        pipet.dispense(vol,
                       location=location.bottom(z=mix_height).move(Point(x=x_offset[1])),
                       rate=reagent.flow_rate_dispense)

    pipet.dispense(1,
                   location=location.bottom(z=mix_height).move(Point(x=x_offset[1])),
                   rate=reagent.flow_rate_dispense)

    if blow_out == True:
        pipet.blow_out(location.top(z=blow_out_offset))  # Blow out


def pick_up(pip):
    "pick up tip and if there is none left, prompt user for a new rack"
    #  nonlocal tip_track
    if not ctx.is_simulating():
        if tip_track['counts'][pip] == tip_track['maxes'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before             resuming.')
            pip.reset_tipracks()
            tip_track['counts'][pip] = 0
    pip.pick_up_tip()


# # Load labware and modules

# ##  Load sample racks

# ## Importing custom labware in Jupyter notebook
# Some labware in intentionaly created by CHER Lab although this file could have been imported from others.

# # Load pipettes

# In[15]:


################################################################################
# Declare which reagents are in each reservoir as well as deepwell and elution plate

# setup samples and destinations
sample_sources_full = ot2lib.generate_source_table(cf.source_racks)
sample_sources = sample_sources_full[:cf.NUM_SAMPLES]
destinations = cf.dest_plate.wells()[:cf.NUM_SAMPLES]

p1000 = cf.ctx.load_instrument('p1000_single_gen2', 'left', tip_racks=cf.tips1000)  # load P1000 pipette
p20 = cf.ctx.load_instrument('p20_single_gen2', 'right', tip_racks=cf.tips20)

# used tip counter and set maximum tips available
tip_track = {
    'counts': {p1000: 0},  # p1000: 0},
    'maxes': {p1000: len(cf.tips1000) * 96}  # ,p20: len(tips20)*96,
}
tip_track = {
    'counts': {p1000: 0, p20: 0},  # p1000: 0},
    'maxes': {p1000: len(cf.tips1000) * 96,
              p20: len(cf.tips20) * 96}  # ,p20: len(tips20)*96,
}


# # Je refais la fonction de calcul
# Je veux que la fonction de calcul dépende de mesures plus simples à prendre. Il est plus simple de mesurer une hauteur ou un dimaètre qu'une surface. 
# J'ai un tube cylindrique à fond conique.
#   - section sup du diamètre sup
#   - hauteur du cone
# On va utiliser la courbe mesurée pour corriger l'équation théorique. Pour un volume donné, on cherche le volume mesuré juste au dessus et on retire la valeur de l'écart (et si on est en fin de liste, on retient la dernière corection). 
# 
# Création d'une fonction évoluée `get_pipetting_heigh()`. Elle retourne toutes les hauteurs de pipettage.
# 
# 

# # Dispensation du Binding Solution en avec diminution progressive de la hauteur d'aspiration. Le Binding Solution est en flacon de 10 ml. 
class ReagentInLabware():
    def __init__(self, ctx, name, flow_rate_aspirate, flow_rate_dispense, rinse, reagent_reservoir_volume,
                 delay, num_wells, h_cono, v_fondo=None, tip_recycling=None
                 , rsup_cono=None
                 , correction_measures=None
                 , verbose=False):

        """
        correction_measures : a list of measured values for a gradient of volume ([volume1,  height_mm1]...]
        correction_measures is a(list of list)  : [[ml1, mm1]; [ml2, mm2]...]
            ml1 : volume 1 in microl put in the vial, 
            mm1 : height measure in mm
            ml2 : volume 2 in microl put in the vial, 
            mm2 : height measure in mm
        
        If correction_measures and deltas are set, a corresponding value (delta) is substracted to improve the 
        theoretical value.
        
        I give up the usage of v_fondo, as this should be calculated. I introduce v_cono as ca calculation 
        
        ctx : context.
        """
        self.ctx = ctx
        self.name = name
        self.flow_rate_aspirate = flow_rate_aspirate
        self.flow_rate_dispense = flow_rate_dispense
        self.rinse = bool(rinse)
        self.reagent_reservoir_volume = reagent_reservoir_volume
        self.delay = delay
        self.num_wells = num_wells
        self.col = 0
        self.vol_well = 0  # volume courant
        self.h_cono = h_cono
        self.rsup_cono = rsup_cono
        if v_fondo:
            self.v_cono = v_fondo
        else:
            self.v_cono = (self.h_cono * math.pi * self.rsup_cono ** 2) / 3
            print("Conical volume has been calculated to : ", self.v_cono)
        self.unused = []
        self.tip_recycling = tip_recycling
        self.vol_well_original = reagent_reservoir_volume / num_wells

        self.correction_measures = correction_measures
        self.theo_lst = []  # Theoretical heights
        self.delta_lst = []  # differences between Theoretical et measured heights.
        self.verbose = verbose
        self.calculations_done = False
        self.update()  # calculs ?

    def set_volume(self, vol):
        "fill reagent to a volume"
        self.vol_well = vol

    def update(self):
        "Include here calculations."
        pass

    def execute_additional_calculations(self):
        """This calculate the correction for heights."""

        saved_val = self.vol_well
        for i, (vol, mesure_mm) in enumerate(self.correction_measures):
            th = self.liquid_level_height(vol)
            dlt = th - mesure_mm
            self.theo_lst.append(th)
            self.delta_lst.append(dlt)
            if self.verbose:
                print(
                    f"Calc. correction : vol = {vol} µl ; theo = {th} ; measured = {mesure_mm} ; correction = {dlt} mm")
            self.set_volume(saved_val)
            if self.verbose:
                print()
        self.calculations_done = True

    def liquid_level_height(self, volume) -> float:
        """Return the height in mm from the bottom of the vial to the level of the liquid for a given volume
        - volume  : microliters
        """
        #         self.verbose = True #  if volume > 4000 else False
        if self.verbose:
            print(f"For vol = {volume}. ", end="")
        if volume < self.v_cono:
            # We are in conical part
            if self.verbose: print("In conical part. ", end="");
            try:
                theoretical_h = math.pow(3 * volume / (math.pi * (self.rsup_cono / self.h_cono) ** 2), 1 / 3)
            except ValueError as data:
                print("Erreur mathématique ", data.args)
                print("volume =", volume)
        else:
            # we are in the top part
            if self.verbose: print("In cylinder part. ", end="");
            h_in_cylinder = (volume - self.v_cono) / (math.pi * (self.rsup_cono * self.rsup_cono))
            theoretical_h = self.h_cono + h_in_cylinder

        if self.verbose: print("theoretical_h = ", theoretical_h);

        h = theoretical_h

        # correction by a set of measures :     
        if self.calculations_done and self.correction_measures and self.delta_lst:
            AA = [measure[0] for measure in self.correction_measures if measure[0] < volume]
            position_of_correction = len(AA)
            if position_of_correction >= len(self.delta_lst):
                position_of_correction -= 1
            h = theoretical_h - self.delta_lst[position_of_correction]
            if self.verbose:
                print("Theory", theoretical_h,
                      "Position_of_correction", position_of_correction,
                      "Valeur de correction", self.delta_lst[position_of_correction],
                      "Valeur de h corrigée", h)

        return h

    def pipetting_height(self, aspirated_volume, min_height=0.5,
                         min_height_for_correction=0, z_offset=-2
                         , consultative_mode=False) -> (float, bool):
        """Return the height as a positive value in mm where liquid will be pipetted, then the change flag.
        
        This values is zero at the bottom of the vial.
        This function requires that the vial is not empty.
        
        z_offset = (usually neg value in mm) : diminish height in order to secure pipetting.

        min_height_for_correction (mm) : below this value, there is no advantage to optimize pipetting height ; 
        so return min_height.
        consultative_mode : if True, will not modify the volume at the end of pipetting.
  
  """
        if self.vol_well <= 0:
            raise ValueError("Well is empty ; You should use self.set_volume()")
        #         self.verbose = True if self.vol_well < 300 else False

        if self.verbose:
            self.ctx.comment('\nRemaining volume: ' + str(self.vol_well) +
                             '  Needed volume: ' + str(aspirated_volume));

        # Le puits est-il assez remplis pour fournir le volume demandé ?
        if self.vol_well > aspirated_volume:
            col_change = False
        else:
            col_change = True
            self.unused.append(self.vol_well)
            if self.verbose:
                self.ctx.comment('Next column should be picked')
                self.ctx.comment('Previous to change: ' + str(self.col))

        vol_at_end_of_pipetting = self.vol_well - aspirated_volume

        if self.verbose: print("vol_at_end_of_pipetting will be : ", vol_at_end_of_pipetting);

        h = self.liquid_level_height(vol_at_end_of_pipetting) + z_offset

        if h < min_height_for_correction:
            h = 0

        if h < min_height:
            h = min_height
        if not consultative_mode:
            self.vol_well = vol_at_end_of_pipetting
        return h, col_change


# Following is list of measures : (volume of liquid put in the vial, measured height in mm)
measures_for_10_ml_conical_tube = ((0, 0)
                                   , (50, 5)
                                   , (100, 8)
                                   , (150, 10)
                                   , (200, 11.5)
                                   , (400, 16)
                                   , (600, 20)
                                   , (800, 22.5)
                                   , (1000, 25.5)
                                   , (2000, 33.5)
                                   , (3000, 40)
                                   , (5000, 48.5)
                                   , (6000, 53)
                                   , (7000, 57.5)
                                   , (8000, 61.5)
                                   )
# Ci-dessus, on lit que pour 2 ml, la hauteur de liquide est de 33.5 mm, à partir du fond.

# Attention : à ces hauteurs on ajoutera 7.5 mm, Il y aun volume mort équivalent à un cone de 7.5 de haut
# et un rayon de 7.5 environ
measures_for_50_ml_falcon_tube = ((1000, 8)
                                  , (2000, 12)
                                  , (3000, 15)
                                  , (4000, 16.5)
                                  , (5000, 18.5)
                                  , (10000, 28)
                                  , (15000, 38)
                                  , (20000, 46)
                                  , (25000, 56)
                                  , (30000, 65)
                                  , (40000, 82)
                                  , (45000, 91)
                                  , (50000, 99)
                                  )

my_solution = ReagentInLabware(cf.ctx,
                               name='Binding solution'
                               , flow_rate_aspirate=0.5
                               , flow_rate_dispense=0.5
                               , rinse=False
                               , delay=1
                               , reagent_reservoir_volume=10000  # 10 ml
                               , num_wells=1  # num_cols comes from available columns
                               , h_cono=46
                               # La formule générale est V = hauteur * pi * R * R /3
                               #                                ,v_fondo = 46 * math.pi / 3  * (17.82/2) ** 2  # (cone)
                               , rsup_cono=17.82 / 2  # radius of the cone
                               , correction_measures=measures_for_10_ml_conical_tube
                               , verbose=False
                               )  # for a
# .vol_well : volume restant. Initialiser au début au volume de remplissage.
# Cette valeur diminue à chaque pipettage.
# my_solution.set_volume(8000)
# my_solution.do_additional_calculations()


my_falcon_sol = ReagentInLabware(cf.ctx,
                                 name='Binding solution'
                                 , flow_rate_aspirate=0.5
                                 , flow_rate_dispense=0.5
                                 , rinse=False
                                 , delay=1
                                 , reagent_reservoir_volume=50000  # 50 ml
                                 , num_wells=1  # num_cols comes from available columns
                                 , h_cono=19
                                 , rsup_cono=26.1 / 2  # radius of the cone
                                 , correction_measures=measures_for_50_ml_falcon_tube
                                 , verbose=True
                                 )
volume = 600  # volume à distribuer

my_falcon_sol.execute_additional_calculations()
my_falcon_sol.set_volume(50000)
my_falcon_sol.pipetting_height(0, consultative_mode=True)

if p1000.hw_pipette['has_tip']:
    p1000.drop_tip()


nb_tests = 8
nb_disp_per_distribution = 3  # this is MANUAL
distribution_nb = math.ceil(nb_tests / nb_disp_per_distribution)
volume = 260
volume_initial_reactif = 50000
volume_per_distribution = volume * nb_disp_per_distribution

max_of_tests = volume_initial_reactif / volume


# summary
print(f"Le nombre de tests à réaliser est de {nb_tests}")
print(f"Le volume initial de réactif est de {volume_initial_reactif} µl")
print(f"Le nombre de distribution sera {distribution_nb}")
print(f"Le volume pris lors de la distribution sera de {volume_per_distribution} µl")
print(f"Le volume délivré sera de {volume} µl")
print("Vu le volume initial et le volume délivré, le nombre maximum de tests est de : {}".format(int(max_of_tests)))
print("Le volume consommé sera de {} µl".format(nb_tests * volume))

# Déclare a Falcon_50 with Binding solution. 
binding_in_falcon50 = ReagentInLabware(cf.ctx, name='Binding solution'
                                       , flow_rate_aspirate=0.5
                                       , flow_rate_dispense=0.5
                                       , rinse=False
                                       , delay=1
                                       , reagent_reservoir_volume=50000  # 50 ml
                                       , num_wells=1  # num_cols comes from available columns
                                       , h_cono=19
                                       , rsup_cono=26.1 / 2  # radius of the cone
                                       , correction_measures=measures_for_50_ml_falcon_tube
                                       , verbose=True
                                       )
volume = 150  # volume à distribuer
# remplir le flacon
binding_in_falcon50.execute_additional_calculations()
binding_in_falcon50.set_volume(50000)

four_in_one_rack_bottom = 7.7  # mm above the desk

def location():
    height = binding_in_falcon50.pipetting_height(aspirated_volume=volume_per_distribution
                                                  , min_height=1, z_offset=-3)
    return cf.binding_lysis_stock_well.bottom(height[0] + four_in_one_rack_bottom)

source_locations_lst = [location() for _ in range(distribution_nb)]

for loc in source_locations_lst:
    print(loc.point)

# ## Attention Action
if p1000.has_tip:
    p1000.drop_tip()
p1000.pick_up_tip()

for i, well_lst in enumerate(
        ot2lib.chunks(ot2lib.reverse_order_wells(cf.dest_plate, 8)[:nb_tests], nb_disp_per_distribution)):
    print(well_lst)
    # well_lst is a list of wells. We replace it by a list of locations. 
    dest_loca_lst = [well.bottom(2) for well in well_lst]
    print("Pipetting in :", source_locations_lst[i].point)
    # distribute() needs Wells and la list of Wells, 
    # but we can transmit locations and an list of locations.
    p1000.distribute(260, source_locations_lst[i], dest_loca_lst,
                     blowout_location='source well', disposal_volume=0,
                     new_tip='never'
                     )
p1000.drop_tip();

p1000.home()
# # Add samples (200 µl) in deepwell plate
###########################################################################
# STEP 1: Add Samples
############################################################################
nb_tests = 8

STEP = 1
if p1000.hw_pipette['has_tip']:
    p1000.drop_tip()

if True:

    cf.ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'])
    cf.ctx.comment('###############################################')
    # Transfer parameters
    start = datetime.now()
    placer = ot2lib.generator_for_4_racks_of_24(cf.source_racks)

    if True:  # input ("Starting for {} samples ? (write : YES)".format(nb_tests)) == "YES":
        for idx in ot2lib.generate_wells_order(8, 12)[:nb_tests]:
            if not p1000.hw_pipette['has_tip']:
                p1000.pick_up_tip()
            input_well = placer.__next__()
            print("Take from {}, and transfer to {}".format(input_well, cf.dest_plate.wells()[idx]))

            move_vol_multichannel(cf.ctx, p1000, reagent=samples, source=input_well, dest=cf.dest_plate.wells()[idx],
                                  vol=200,
                                  air_gap_vol=30, x_offset=[0, 0],
                                  pickup_height=1,
                                  rinse=True,
                                  # rinse = samples.rinse,
                                  disp_height=-15,
                                  blow_out=True, touch_tip=False, verbose=False, blow_out_offset=-10)
            p1000.drop_tip()
            tip_track['counts'][p1000] += 1
            print()
            # Time statistics
    end = datetime.now()
    time_taken = (end - start)
    comment = 'Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + 'took ' + str(time_taken)
    cf.ctx.comment(comment)
    STEPS[STEP]['Time:'] = str(time_taken)