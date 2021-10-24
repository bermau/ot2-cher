# Define Reagents as objects with their properties
import itertools
class ReagentInLabware():
    def __init__(self,  name, flow_rate_aspirate, flow_rate_dispense, rinse, reagent_reservoir_volume, 
                 delay, num_wells, h_cono, v_fondo, tip_recycling = None , rsup_cono= None):
        # note : Le none de tip_recycling été noté 'note'
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
    
    def set_volume(vol):
        self.vol_well = vol           
    
    def update(self):
        pass
        
# Custom functions
def generate_source_table(source):
    """
    Concatenate the wells from the different origin racks
    """
    for rack_number in range(len(source)):
        if rack_number == 0:
            s = source[rack_number].wells()
        else:
            s = s + source[rack_number].wells()
    return s


def calc_height(reagent, cross_section_area, aspirate_volume, min_height=0.5):
    
    global ctx    # ????
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
                #- reagent.h_cono
        reagent.vol_well = reagent.vol_well - aspirate_volume
        ctx.comment('Remaining volume:' + str(reagent.vol_well))
        if height < min_height:
            height = min_height
        col_change = True
        
    else:
        height = (reagent.vol_well - aspirate_volume - reagent.v_cono) / cross_section_area #- reagent.h_cono
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
## Functions to manage the local order of run
#####################################################

# Par défaut, la fonction wells() affiche les puits ainsi :
# " A1, A2, A3...A12, B1, B2.

# generate the order of the wells walking bottom to top then left to right
# Order is : generate_wells_order(8,12) : [7, 6, 5, 4, 3, 2, 1, 0, 15, 14, 13, 12,
# 11, 10, 9, 8, ...
# fist position (bottom left is 0)
# return and index 

# La fonction suivante remplace la fonction generate_wells_order(3, 4)
# Attention : pour l'instant elle renvoie une liste de liste
def list_of_index_lists(rows, cols, sens='landscape'):
    """return a list of lists of integers representing the indexes to select
    wells in our local right order.

    rows: number of rows
    cols : number of columns

    sens :
        'lanscape' : plate is filled row b row (from A1 to A12, then B1 to B12)...
        'portrait' : plate is filled col by col, from H1 to A1 then H2 to A2...
    return : a list of lists

    >>> list_of_index_lists(3, 4)
    [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
    >>> list_of_index_lists(2, 3)
    [[0, 1, 2], [3, 4, 5]]
    >>> list_of_index_lists(2, 3, sens='portrait')
    [(3, 0), (4, 1), (5, 2)]
    """
    numbers = list(range(rows * cols))
    ret = []
    for i in range(0, numbers[-1], cols):
        ret.append(numbers[i:i + cols])

    if sens == 'landscape':
        return ret
    elif sens == 'portrait':
        return list(list(zip(ret[1], ret[0])))



### Créer un générateur

# Repartition of samples of several racks
# Case of 4  4x6 racks
#  disposition of racks on the OT :
    # rack 1  | rack 2
    # rack 3  | rack 4
def generator_for_4_racks_of_24(racks):
    """up to 96 tubes are loaded in 4 24 tubes racks.
    The first tube is H1 in rack3 (first bottom left if the plate is in landscape position),
    The second tube is G1 in rack3, fifth tube is D1 in rack 1, sixth is C1 in rack 1...

    racks : a list of 4 racks Labware
    Returns : a single Well each time.

    How to use this function ?

    # Repartition of samples of several racks
    # Case of 4  4x6 racks
    #  disposition of racks on the OT :
    # rack 1  | rack 2
    # rack 3  | rack 4
    # in ou lab (CHER), wells are used in the following order : D1 of rack3, C1 of rack3, B1 of rack3,
     A1 of rack3, then D1 of rack 1 ...
    TODO explaination

    source_racks  = [ source1, source2, source3, source4)
    placer = ot2lib.generator_for_4_racks_of_24(source_racks)
    [ input_well = placer.__next__() for _ in range(N) ]
    """
    counter = 0

    for rack in racks:
        rack.used_pos = 0
        lst = list_of_index_lists(4, 6)  # fournit une [list, list, list]
        rack.ordered_wells = grouped_reverse(list(itertools.chain(*lst)), 4)  # convert to simple list

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
def grouped_reverse(lst: list, group_size: int) -> list:
    """number of row is synonymous of columns.
    reverse each group of group_size elements. group_size is usually the number of rows.
    grouped_reverse
    >>> grouped_reverse(list("ABCDEFGH"), 4)
    ['D', 'C', 'B', 'A', 'H', 'G', 'F', 'E']

    example of use :
    grouped_reverse(source_racks[0].wells(), 4) # where source_racks[0] is a LabWare
    """
    return [elt for line in chunks(lst, group_size) for elt in line[:: -1]]

# DECK  SUMMARY : 
def labware_short_name(string, nb_cars):
    """Return a max of nb_cars. Or return beginning and end of the 
    string if string is too long
    
    >>> labware_short_name("atoolongnametoenterinthislittlecase", 25)
    'atoolongna...islittlecase'
    """
    length = len(string)
    if length <= nb_cars:
        return string
    else:
        return string[:10] + '...' + string[-(nb_cars -3 -10):]
    
def deck_summary(ctx):
    """Display the deck and its labware"""
    for pos_range  in [[10, 11, 12], [7, 8, 9], [4, 5, 6], [1, 2, 3]]:
        print('| ', end = '')
        for pos in pos_range:
            rack = ctx.deck[pos]            
            if rack:
                try:
                    print("{:<27}".format(str(pos) + ": "
                          + labware_short_name(rack._name,23 )), end=' | ')          
                except:
                    pass  # Trash has no _name.
                    print("{:<27}".format(str(pos) + ": Trash"), end=' | ')
            else:
                print("{:<27}".format(str(pos) + ': ***'), end=' | ')
        print()

if __name__ == '__main__':
    print("Demonstration :")

    # placer = ot2lib.generator_for_4_racks_of_24(cf.source_racks)