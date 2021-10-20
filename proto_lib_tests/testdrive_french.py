# This code is originaly from :https://protocols.opentrons.com/protocol/testdrive

def get_values(*names):
    import json
    _all_values = json.loads("""{"well_plate":"corning_96_wellplate_360ul_flat","pipette":"p300_single_gen2",
    "tips":"opentrons_96_filtertiprack_200ul","pipette_mount":"left"}""")
    return [_all_values[n] for n in names]


from opentrons.types import Point

metadata = {
    'protocolName': 'OT-2 Guided Walk-through',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [well_plate, pipette, tips, pipette_mount] = get_values(  # noqa: F821
        "well_plate", "pipette", "tips", "pipette_mount")

    # load labware
    plate = ctx.load_labware(well_plate, '1')
    tiprack = ctx.load_labware(tips, '2')

    # load instrument
    pip = ctx.load_instrument(pipette, pipette_mount, tip_racks=[tiprack])

    # protocol
    test_well = plate.wells()[0]

    pip.pick_up_tip()

    ctx.pause('''Bienvenue dans le protocole de présentation de OT-2-
                    Ceci est la fonction "Pause".
                    Des pauses peuvent être mises à tout moment au cours d'un protocole
                    pour remplacer les plaques, les réactifs, pour retirer les plaques ,
                    ou pour tout autre cas où une intervention humaine
                    est nécessaire. Les protocoles continuent après une « Pause » lorsque
                    le bouton « Resume (Reprendre) » est sélectionné. Sélectionnez « Resume »
                    pour voir plus de fonctionnalités OT-2.''')


    ctx.pause('''Les pipettes peuvent se déplacer presque n'importe où dans l'OT-2-
                    Sélectionnez « Reprendre » pour voir le liquide être aspiré par la pipette
                    sur le côté du puits, et distribué au sommet du puits. ''')

    if well_plate == 'corning_384_wellplate_112ul_flat':
        dimension = int(test_well.length)/2

    elif well_plate == 'nest_96_wellplate_2ml_deep':
        dimension = int(test_well.length)/2

    elif well_plate == 'usascientific_96_wellplate_2.4ml_deep':
        dimension = int(test_well.length)/2

    else:
        dimension = int(test_well.diameter)/2

    well_vol = test_well.geometry.max_volume
    vol = well_vol/1.5 if well_vol < pip.max_volume else pip.max_volume/1.5

    pip.move_to(plate['A1'].top())
    pip.aspirate(vol, test_well.bottom().move(Point(x=(dimension-1.1))))
    pip.dispense(vol, test_well.top())
    pip.aspirate(vol, test_well.bottom().move(Point(x=((dimension-1.1)*-1))))
    pip.dispense(vol, test_well.top())

    ctx.pause('''Maintenant nous mélangeons trois fois à vitesse normale.''')
    pip.mix(3, vol, test_well)

    ctx.pause('''Maintenant, réduisont la vitesse du flux de la pipette d'un facteur 2.''')
    pip.flow_rate.aspirate = 0.5*pip.flow_rate.aspirate
    pip.flow_rate.dispense = 0.5*pip.flow_rate.dispense
    for _ in range(2):
        pip.aspirate(vol, test_well)
        pip.dispense(vol, test_well.top())

    ctx.pause('''Doublons la vitesse du flux de la pipette.''')
    pip.flow_rate.aspirate = 4*pip.flow_rate.aspirate
    pip.flow_rate.dispense = 4*pip.flow_rate.dispense
    for _ in range(2):
        pip.aspirate(vol, test_well)
        pip.dispense(vol, test_well.top())

    ctx.pause("""La fonction "toucher" ("touch tip" en anglais) peut être
                    appelée après l'aspiration ou la distribution. Le toucher 
                    consiste à déplacer la pipette de la pipette sur les quatre 
                    bords opposés d'un puits, pour faire tomber
                    toutes les gouttelettes qui pourraient pendre de la pointe.
                    Sélectionnez "Resume" pour voir une démonstration de "toucher""")


    for _ in range(2):
        pip.aspirate(vol, test_well)
        pip.touch_tip()
        pip.dispense(vol, test_well.top())

    ctx.pause('''La fonction "souffler" peut être appelée après dispensation d'un 
                   liguide. Souffler une petit quantité d'air par l'extrémité de
                   la pointe permet de s'assurer que toute le liquid est expulsé. 
                   Sélectionnez "Resume" pour voir le "souffler''')

    for _ in range(2):
        pip.aspirate(vol, test_well)
        pip.dispense(vol, test_well.top())
        pip.blow_out()

    ctx.pause('''Now lets change the blow out flow rate, and blow out in the
                   trash on Slot 12. ''')

    pip.flow_rate.blow_out = 0.5*pip.flow_rate.blow_out
    pip.transfer(vol, plate.wells()[0], plate.wells()[16], blow_out=True,
                 lowout_location='trash', new_tip='never')
    pip.flow_rate.blow_out = 2*pip.flow_rate.blow_out

    ctx.pause('''Maintenant jetons le cône à la poubelle et prenons en un autre.''')
    pip.drop_tip()
    pip.pick_up_tip()
    pip.move_to(plate['A1'].top())

    ctx.pause('''The airgap function can be called after aspirating -
                 When dealing with certain liquids, you may need to aspirate
                 air after aspirating the liquid to prevent it from sliding out
                of the pipette’s tip. We will use the delay function to
                pause for 5 seconds after air-gapping. Delays are similar to
                pauses except for there is no `Resume` button that has to be
                selected by the user. Delays are especially useful for
                incubation periods, or after aspirating viscous liquid
                to achieve full volume.''')
    airgap = pip.max_volume/3
    for _ in range(3):
        pip.aspirate(vol/3, test_well)
        pip.air_gap(airgap)
        ctx.delay(seconds=5)
        pip.dispense(vol/2+airgap, test_well.top())

    ctx.pause('We can even airgap within the same tip')

    airgap = pip.max_volume/8
    for _ in range(2):
        pip.aspirate(vol/8, plate.wells()[0])
        pip.air_gap(airgap)
    ctx.delay(seconds=5)
    pip.blow_out()
    ctx.pause('''Now let's return the tip for later on in the protocol,''')
    pip.return_tip()
    pip.pick_up_tip()

    ctx.pause('''Now we can consolidate and distribute.
                 Volumes going to the same destination well are combined
                 within the same tip, so that multiple aspirates can be
                 combined to a single dispense (consolidation).
                 For the distribute function, volumes from the same source well
                 are combined within the same tip, so that one aspirate can
                 provide for multiple dispenses. Click `Resume` to see
                 a consolidate function call followed by a distribute''')

    pip.consolidate(vol/8,
                    plate.wells()[0:8], plate.wells()[8], new_tip='never')

    pip.drop_tip()
    ctx.pause('''Before we distribute, let's use our parked tip from before''')
    pip.pick_up_tip(tiprack.wells()[1])
    pip.distribute(vol/8,
                   plate.wells()[8], plate.wells()[0:8], new_tip='never')
    pip.drop_tip()
