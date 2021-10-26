# Manipulation pour Laboratoire du Centre hospitalier Emile Roux (CHER)
# I included all my tools previously written in ot2_functions.py

# Define Reagents as objects with their properties
import itertools

from opentrons.types import Point
import json
import os

num_samples_without_ctrl = 3

# Unused
class ReagentInLabware:
    def __init__(self, name, flow_rate_aspirate, flow_rate_dispense, rinse, reagent_reservoir_volume,
                 delay, num_wells, h_cono, v_fondo, tip_recycling=None, rsup_cono=None):
        self.name = name
        self.flow_rate_aspirate = flow_rate_aspirate
        self.flow_rate_dispense = flow_rate_dispense
        self.rinse = bool(rinse)
        self.reagent_reservoir_volume = reagent_reservoir_volume
        self.delay = delay
        self.num_wells = num_wells
        self.col = 0
        self.vol_well = 0
        self.h_cono = h_cono
        self.v_cono = v_fondo
        self.unused = []
        self.tip_recycling = tip_recycling
        self.vol_well_original = reagent_reservoir_volume / num_wells
        self.rsup_cono = rsup_cono
        self.update()

    def set_volume(self, vol):
        self.vol_well = vol

    def update(self):
        pass

# Unused
def calc_height(reagent, cross_section_area, aspirate_volume, min_height=0.5):
    global ctx  # ????
    ctx.comment('Remaining volume ' + str(reagent.vol_well) +
                '< needed volume ' + str(aspirate_volume) + '?')
    if reagent.vol_well < aspirate_volume:
        reagent.unused.append(reagent.vol_well)
        ctx.comment('Next column should be picked')
        ctx.comment('Previous to change: ' + str(reagent.col))
        # column selector position; intialize to required number
        reagent.col = reagent.col + 1
        ctx.comment(str('After change: ' + str(reagent.col)))
        reagent.vol_well = reagent.vol_well_original
        ctx.comment('New volume:' + str(reagent.vol_well))
        height = (reagent.vol_well - aspirate_volume - reagent.v_cono) / cross_section_area
        # - reagent.h_cono
        reagent.vol_well = reagent.vol_well - aspirate_volume
        ctx.comment('Remaining volume:' + str(reagent.vol_well))
        if height < min_height:
            height = min_height
        col_change = True

    else:
        height = (reagent.vol_well - aspirate_volume - reagent.v_cono) / cross_section_area  # - reagent.h_cono
        reagent.vol_well = reagent.vol_well - aspirate_volume
        ctx.comment('Calculated height is ' + str(height))
        if height < min_height:
            height = min_height
        ctx.comment('Used height is ' + str(height))
        col_change = False

    return height, col_change


##########
# pick up tip and if there is none left, prompt user for a new rack
def pick_up(pip):
    #  nonlocal tip_track
    if not ctx.is_simulating():
        if tip_track['counts'][pip] == tip_track['maxes'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
            resuming.')
            pip.reset_tipracks()
            tip_track['counts'][pip] = 0
    pip.pick_up_tip()


#####################################################
## Functions to manage the CHER local order of run
#####################################################

# Par défaut, la fonction wells() affiche les puits ainsi :
# " A1, A2, A3...A12, B1, B2.

# generate the order of the wells walking bottom to top then left to right
# Order is : generate_wells_order(8,12) : [7, 6, 5, 4, 3, 2, 1, 0, 15, 14, 13, 12,
# 11, 10, 9, 8, ...
# first position (bottom left is 0)
# return and index

# La fonction suivante remplace la fonction generate_wells_order(3, 4)
def list_of_index_lists(rows, cols, sens='landscape'):
    """return a list of lists of integers representing the indexes to select
    wells in our local right order.

    rows: number of rows
    cols : number of columns

    sens :
        'lanscape' : plate is filled row b row (from A1 to A12, then B1 to B12)...
        'portrait' : plate is filled col by col, from H1 to A1 then H2 to A2...
    return : a list integers

    >>> list_of_index_lists(3, 4)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    >>> list_of_index_lists(2, 3)
    [0, 1, 2, 3, 4, 5]
    >>> list_of_index_lists(2, 3, sens='portrait')
    [3, 0, 4, 1, 5, 2]
    """
    numbers = list(range(rows * cols))
    ret = []
    for i in range(0, numbers[-1], cols):
        ret.append(numbers[i:i + cols])

    if sens == 'landscape':
        pass
    elif sens == 'portrait':
        ret = list(list(zip(ret[1], ret[0])))
    # next list turn a list of lists into a list of simple elements.
    return list(itertools.chain(*ret))


# Repartition of samples on several racks
def generator_for_4_racks_of_24(racks):
    """Up to 96 tubes are loaded in 4 24 tubes racks.
    In our lab, the first tube is H1 in rack3 (first bottom left if the plate is in landscape position),
    The second tube is G1 in rack3, fifth tube is D1 in rack 1, sixth is C1 in rack 1...

    racks : a list of 4 racks Labware
    Returns : a single Well each time.

    How to use this function ?

    # Repartition of samples of several racks
    # Case of 4  4x6 racks
    #  disposition of racks on the OT :
    # rack 1  | rack 2
    # rack 3  | rack 4
    # in our lab (CHER), wells are used in the following order : D1 of rack3, C1 of rack3, B1 of rack3,
     A1 of rack3, then D1 of rack 1 ...
    # The wells() method from opentrons.protocol_api.labware.Labware return a list of index in the following order :
    # A1, B2, C3... then A2, B2, C2...

    source_racks  = [source1, source2, source3, source4]
    placer = generator_for_4_racks_of_24(source_racks)
    wells_lst = [ input_well = placer.__next__() for _ in range(N) ]
    """
    counter = 0
    for rack in racks:
        rack.used_pos = 0
        lst = list_of_index_lists(4, 6)  # fournit une liste
        rack.ordered_wells = grouped_reverse(lst, 4)  # convert to simple list

    for rack in [racks[2], racks[0]] * 6:
        for i in range(4):
            counter += 1
            rack.used_pos += 1
            yield rack.wells()[rack.ordered_wells[rack.used_pos - 1]]

    for rack in [racks[3], racks[1]] * 6:
        for i in range(4):
            counter += 1
            rack.used_pos += 1
            yield rack.wells()[rack.ordered_wells[rack.used_pos - 1]]


def chunks(lst, n_max):
    """Yield successive n_max-sized chunks from lst.
    Last item cant have less than n_max elements
    >>> list(chunks(['a', 'b', 'c', 'd', 'e', 'f', 'g'], 3))
    [['a', 'b', 'c'], ['d', 'e', 'f'], ['g']]
    """
    for i in range(0, len(lst), n_max):
        yield lst[i:i + n_max]


# reverse_order_wells is replace by following
# Cette fonction permet de corriger l'ordre d'utilisation des puits pour notre labo.
def grouped_reverse(lst: list, group_size: int) -> list:
    """Reverse each group of group_size elements in a list.

    group_size is usually the number of rows.
    >>> grouped_reverse(list("ABCDEFGH"), 4)
    ['D', 'C', 'B', 'A', 'H', 'G', 'F', 'E']

    example of use :
    grouped_reverse(source_racks[0].wells(), 4) # where source_racks[0] is a LabWare
    """
    return [elt for line in chunks(lst, group_size) for elt in line[:: -1]]


# DECK  SUMMARY : display a graphical aspect of the deck.
def labware_short_name(string, nb_cars):
    """Return a max of nb_cars, the beginning and end of the
    string if the tring is too long

    >>> labware_short_name("atoolongnametoenterinthislittlecase", 25)
    'atoolongna...islittlecase'
    """
    length = len(string)
    if length <= nb_cars:
        return string
    else:
        return string[:10] + '...' + string[-(nb_cars - 3 - 10):]


def deck_summary(ctx):
    """Display the deck and its labware"""
    for pos_range in [[10, 11, 12], [7, 8, 9], [4, 5, 6], [1, 2, 3]]:
        print('| ', end='')
        for pos in pos_range:
            rack = ctx.deck[pos]
            if rack:
                try:
                    print("{:<27}".format(str(pos) + ": "
                                          + labware_short_name(rack._name, 23)), end=' | ')
                except:
                    pass  # Trash has no _name.
                    print("{:<27}".format(str(pos) + ": Trash"), end=' | ')
            else:
                print("{:<27}".format(str(pos) + ': ***'), end=' | ')
        print()


def get_values(*names):
    import json
    _all_values = json.loads("""{
    "num_samples":5,
    "vol_sample":200,
    "vol_lys_buffer":260,
    "asp_height":5,
    "add_neg":1,
    "p1000_mount":"left","p1000_type":"p1000_single_gen2","tip_track":false}""")
    return [_all_values[n] for n in names]


# os.sys.path.insert(1, os.path.realpath("../my_lib/"))
# import ot_2_functions as ot2func

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
    [vol_sample, vol_lys_buffer, asp_height, add_neg,
     p1000_mount, p1000_type,
     tip_track] = get_values(
        'vol_sample', 'vol_lys_buffer',
        'asp_height', 'add_neg', 'p1000_mount', 'p1000_type',
        'tip_track')
    experiment = {"plate_binding_solution": True,
                  "transfert_samples": False}
    num_samples = num_samples_without_ctrl + add_neg

    ctx.pause("Ce programme est prévu pour {} tests (hors contrôles)".format(num_samples_without_ctrl))
    ctx.pause("Tout le matériel doit être en place.")
    ctx.pause("Confirmer (Resume) pour démarrer {} puits pour le protocole, sinon appuyer sur Stop".format(num_samples))

    def comment(msg):
        longueur = len(msg)
        ctx.comment("*" * longueur)
        ctx.comment(msg)
        ctx.comment("*" * longueur)

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
    # Tips
    tipracks1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', slot, 'Pointes 1000µl')
                    for slot in ['10']]

    # Pipette
    p1000 = ctx.load_instrument(p1000_type, p1000_mount,
                                tip_racks=tipracks1000)

    # setup samples and reagents

    # destination wells list. Destination sur la plaque de DeepWell
    # leave controls empty
    dests_w_lst = grouped_reverse(deepwell_lw.wells(), 8)[:num_samples]
    print("DEST", dests_w_lst)

    # Le truc qui tourne la géométrie dans notre sens.
    placer = generator_for_4_racks_of_24(source_racks)
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
        tip_log['count'] = {p1000: 0}  # tip_log['count'] = {p1000: 0, p300: 0}

    tip_log['tips'] = {
        p1000: [tip for rack in tipracks1000 for tip in rack.wells()],
        # p300: [tip for rack in tipracks300 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p1000]  # [p1000, p300]
    }

    # Display the map of the deck with labware
    deck_summary(ctx)

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
            ctx.comment("COM : " + str(i + 1))
            pick_up(p1000)
            p1000.transfer(vol_lys_buffer, lys_buffer[i // 24], d.bottom(5),
                           air_gap=50, new_tip='never')
            p1000.air_gap(50)  # air_gap avant de retourner à la poubelle
            p1000.drop_tip()

    # transfer samples
    if experiment["transfert_samples"]:
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
