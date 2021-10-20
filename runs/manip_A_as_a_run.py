# Manipulation pour CHER

num_samples_without_ctrl = 3


def get_values(*names):
    import json
    _all_values = json.loads("""{
    "num_samples":5,
    "vol_sample":200,
    "vol_lys_buffer":260,
    "asp_height":5,
    "add_neg":1,
    "p300_mount":"right","p300_type":"p300_single_gen2",
    "p1000_mount":"left","p1000_type":"p1000_single_gen2","tip_track":false}""")
    return [_all_values[n] for n in names]

from opentrons.types import Point
import json
import os

os.sys.path.insert(1, os.path.realpath("../my_lib/"))
import ot_2_functions as ot2func

# metadata
metadata = {
    'protocolName': 'Tools for OT-2',
    'author': 'Bertrand Maubert',
    'source': 'Laboratoire du Centre hospitalier Emile Roux- Le Puy en Velay',
    'apiLevel': '2.10',  # Original 2.0
    'description': """Tools for OT-2 and Protocol for Kingfisher sample setup (A). 
Protocol for Kingfisher sample setup (A) - Viral/Pathogen II Kit (ref A48383) 
Adapted from covid19clinic project"""
}


def run(ctx):
    [vol_sample, vol_lys_buffer,  asp_height, add_neg,
     p300_mount, p300_type, p1000_mount, p1000_type,
     tip_track] = get_values(
        'vol_sample', 'vol_lys_buffer',
        'asp_height', 'add_neg','p300_mount', 'p300_type', 'p1000_mount', 'p1000_type',
        'tip_track')
    experiment = {"plate_binding_solution": True,
                  "transfert_samples": False}
    # num_samples = int(input("nb tests"))
    num_samples = num_samples_without_ctrl + add_neg

    ctx.pause("Ce programme est prévu pour {} tests (hors contrôles)".format(num_samples_without_ctrl))
    ctx.pause("Tout le matériel doit être en place.")
    ctx.pause("Confirmer (Resume) pour démarrer {} le protocole, sinon appuyer sur Stop".format(num_samples))

    def comment(msg):
        l = len(msg)
        ctx.comment("*" * l)
        ctx.comment(msg)
        ctx.comment("*" * l)

    # load labware (lw)  #  TODO : mettre la vraie définition de plaque de Thermo
    deepwell_lw = ctx.load_labware('nest_96_wellplate_2ml_deep', '3', 'Deepwell plate')
    # sources of samples : 4 racks of Eppendorf 
    # slots sont numérotés et disposés ainsi
    #    rack 1 | rack 2
    #    rack 3 | rack 4
    rack4in1_name = 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap'
    source_racks = [ctx.load_labware(rack4in1_name, slot, 'Echantillons ' + str(i + 1))
                    for i, slot in enumerate(['4', '5', '1', '2'])]
    
    # pour solution de binding/lyse
    reservoir = ctx.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', '6',
                                 'reagent reservoir')

    tipracks1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', slot, 'Pointes 1000µl')
                    for slot in ['10']]

    # load pipette
    p1000 = ctx.load_instrument(p1000_type, p1000_mount,
                                tip_racks=tipracks1000)

    # setup samples and reagents

    # ot2lib.generate_wells_order(8, 12)[:nb_tests]:
    dests_w_lst = ot2func.grouped_reverse(deepwell_lw.wells(), 8)[:num_samples]  # leave controls empty
    print("DEST", dests_w_lst)

    # Le truc qui tourne la géométrie dans notre sens.
    placer = ot2func.generator_for_4_racks_of_24(source_racks)
    # sources = [well for rack in source_racks for well in rack.wells()][:num_samples]
    # cet ordre n'est pas adapté.
    # deistation wells list
    sample_w_lst = [placer.__next__() for _ in range(num_samples)]


    lys_buffer = reservoir.wells('B4')
    # tip log
    tip_log = {'count': {}}
    folder_path = '/data/A'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips1000' in data:
                    tip_log['count'][p1000] = data['tips1000']
                else:
                    tip_log['count'][p1000] = 0
    else:
        tip_log['count'] = {p1000: 0}      # tip_log['count'] = {p1000: 0, p300: 0}

    tip_log['tips'] = {
        p1000: [tip for rack in tipracks1000 for tip in rack.wells()],
        # p300: [tip for rack in tipracks300 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p1000]   # [p1000, p300]
    }

    # Display the map of the deck with labware
    ot2func.deck_summary(ctx)

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1


    # transfer lysis/binding buffer
    if experiment["plate_binding_solution"]:
        comment("Transfer Binding Solution")
        for i, d in enumerate(dests_w_lst):
            ctx.comment("COM : "+str(i+1))
            pick_up(p1000)
            p1000.transfer(vol_lys_buffer, lys_buffer[i//24], d.bottom(5),
                           air_gap=50, new_tip='never')
            p1000.air_gap(50) # air_gap avant de retourner à la poubelle
            p1000.drop_tip()

    # transfer samples
    if experiment["transfert_samples"] :
        comment("Transfer sample")
        for s, d in zip(sample_w_lst, dests_w_lst):
            pick_up(p1000)
            # Régler la hauteur avec : .bottom().move(Point(x=(-1.5))))
            p1000.transfer(vol_sample, s.bottom(asp_height).move(Point(x=(-1.5))), d.bottom(10),
                          air_gap=50, new_tip='never')
            p1000.air_gap(50)
            p1000.drop_tip()


    ctx.comment('Récupérer la plaque, ajouter le mélange MS2/PK puis, '
                'placer la plaque dans le KinkFisher. ')

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips1000': tip_log['count'][p1000],
            # 'tips300': tip_log['count'][p300]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)