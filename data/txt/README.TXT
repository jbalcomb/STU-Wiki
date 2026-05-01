
                   M a s t e r   o f   M a g i c
                            Version 1.3.1

-----------------------
Problem Troubleshooting
-----------------------

Please make sure you have the following memory available:

583K CONVENTIONAL MEMORY
2.7M EXPANDED MEMORY

Refer to your DOS manual for information on memory management.

If you use the QEMM memory manager, there are a couple of
problems that you should be aware of. 

1. You should not use the STEALTH configuration. This mode 
   is known to cause problems with Master of Magic. You should
   remove the ST:M or ST:F switch from your QEMM386.SYS command 
   line and then re-optimize. If you need help doing this you can
   consult Quarterdeck Office Systems Tech Support at
   (310) 392-9701 from 5:30am to 3:30pm EST.

2. It is not recommended that you use Microsoft's SMARTDRV.EXE or
   SMARTDRV.SYS with the QEMM memory manager.

3. If you use SMARTDRV.EXE or SMARTDRV.SYS, you should disable the
   write cache using the /X switch.

4. Attention owners of the Compaq Presario. If you are not getting any sound
in the game, you may need to make a change to your autoexec.bat file. Check
it for the following line, "set blaster=A220 I5 D1 T5". (Type "type 
autoexec.bat|more" at the c: prompt to bring the file on screen.) If it 
doesn't appear, type "edit autoexec.bat" at the c: prompt, and insert that 
instruction at the first line of the file. You will then have to reboot your 
computer to execute it. We advise those who haven't had experience editing 
files to make a copy of the autoexec.bat file on a disk before making any 
changes to it. Thus, if you make a mistake, you can recopy the file back 
into your root directory and return to where you started.

5. To install and run the CD-ROM version of Master of Magic entirely from 
the hard-drive, follow these steps:
* Make a directory on your hard-drive (ex. MAGIC).
* Change to that directory.
* Type the following at the DOS prompt: "COPY D:\GAME\*.*". This command 
  assumes that "D:" is your CD drive.
* Wait for all of the files to copy (about 25 megs).
* When this is finished, type install and select "Configuration" to
  set your soundcard settings. 
* Once this is done, just type "MAGIC" to start the game!
Note: You can only use itemmake with Master Of Magic stored entirely on your 
hard-drive.

------------------
Manual Corrections
------------------
There have been many changes to the game since the printing of
the manual. Master of Magic contains an on-line help system that
reflects these changes. To access the on-line help, you can
right-click specific portions of the game screen.

---------------------
Sound Troubleshooting
---------------------

If you use a SoundBlaster sound card, you must have your BLASTER
environment variable correctly SET.

If you use a SoundBlaster sound card that is set to IRQ 10, you
may experience problems. Try configuring your card for a lower IRQ.

If you use a Pro Audio Spectrum card, you must have the MVSOUND.SYS
driver properly installed.

If you use a Roland or General MIDI sound card, you may experience
some delays when starting Master of Magic. These cards require a
short initialization period.

If you use a Roland or General MIDI sound card, you may need to turn
your machine off and then back on when changing settings in the
INSTALL program.

--------------
Hints and Tips
--------------
If you would like to skip the intro animation and continue your
current game, you can run the WIZARDS.EXE instead of the MAGIC.EXE.
When you type WIZARDS, the continue save game (SAVE9.GAM) will be
automatically loaded.

---------------------------------------------
Version 1.2 Gameplay Changes and Enhancements
---------------------------------------------

SPECIAL ABILITIES:
-  The Alchemist special ability allows all of your new normal 
   units built to be equipped with +1 magical weapons, as if an 
   alchemist's guild were present in all of the wizard's towns.
-  Archmages gain +50% towards their spell casting skill.
-  Node Mastery makes you immune to having your spells dispelled 
   while in a node.
-  The special ability of Famous now starts you with 10 fame.
-  The Conjurer's bonus of +25% now applies to research of 
   summoning spells, maintenance costs of fantastic creatures, and 
   casting cost for all summoning spells.
-  The Artificer reduces the cost of creating magical items by 50%.
-  The Runemaster ability doubles the wizard's chance to dispel 
   another wizard's enchantment, instead of making the runemaster's 
   spells harder to dispel.
-  The Chaos Mastery, Sorcery Mastery, and Nature Mastery abilities 
   now give the wizard a +15% bonus to his research and casting of 
   spells of the appropriate realm, instead of +10% just to 
   researching.
-  The Channeling special ability now reduces maintenance for all 
   summoned creatures by 50%, in addition to eliminating the range 
   penalties for casting combat spells away from your fortress. The 
   Channeling ability costs 2 picks.
-  The Myrran ability now costs 3 picks.

SPELLS AND MAGIC:
-  A wizard's fortress generates magic power  equal to the number 
   of spell book picks selected when the game begins, instead of 
   the base 5. Myrran wizards then make an additional +5 magical 
   power from their fortress.
-  A wizard's starting spell casting skill is equal to twice the 
   number of spell books chosen when the game begins.
-  Guaranteed spells have been eliminated. Instead a wizard may 
   select one spell for each book he picked above one when the game 
   begins. Wizards who selected 11 picks begins with all common 
   spells, 2 uncommon spells, and one rare spell.
-  The Disjunction spell now has a base cost of 200.
-  The Windwalking spell now has a maintenance cost of 10 mana.
-  The Weakness spell is no longer automatic and requires a save, 
   but the spell does have a -2 resistance penalty.
-  The Starfires spell only costs 5 mana to throw.
-  The Holy Weapon spell now costs 10 mana to throw in combat, 
   50 overland.
-  Great Unsummoning now has a -3 resistance penalty.
-  Guardian Wind has become a common spell and costs 10 mana to 
   cast in combat, 50 mana overland.
-  Guises has been eliminated as a spell, and replaced by Blur. 
   The Blur spell is uncommon sorcery and covers all of your units 
   in a veil of wispy illusion, making it very difficult to see the 
   exact positions of the protected units. As a result, all hits 
   inflicted against the blurred creatures have a 10% chance of 
   just missing. Blur is a global combat spell and costs 25 mana to 
   cast.
-  The Dispel Magic True, Disenchant True, and Disjunction True 
   spells all dispel with a strength equal to 3 times the mana spent 
   on casting the spell.

UNITS AND HEROES:
-  Units may only fire 1 missile attack each turn. Firing a ranged 
   attack ends the unit's turn.
-  Units with lifestealing may still attack with their normal attack
-  Clarification: all animated dead units cost 50% more mana to 
   maintain than the creature's cost before becoming undead, 
   regardless of how the creature become undead ( ghoul, demon 
   lord drain, life drain spell, animate dead spell, etc.).
-  Berserkers have a 7 hand-to-hand, 3 defense, 3 thrown, 7 
   resistance, and cost 120gp.
-  Hammerhands now have a 4 defense.
-  Sky Drakes are now very rare creatures.
-  Death knight's now have a h-to-h attack strength of 9
-  Demon lord now has a -5 save to life stealing
-  Djinns are now very rare creatures.
-  Halflings standard units cost 150% normal
-  Halflings no longer have a +1 defense.
-  Magicians have a 5 strength and Warlocks have a 7 strength.
-  Galleys and Triremes have a 4 defense.
-  Galleys have a 2 range arrow attack with 8 ammo.
-  Gnoll units cost the normal standard unit costs for spearmen, 
   swordsmen, bowmen, halberdiers, and settles.
-  Gnollish wolf riders may now move 3 and have a 7 attack 
   strength.
-  Lizardmen dragon turtles require a stables and an armorer's 
   guild to build.
-  Draconian standard units now fly at a speed of 2.
-  Draconian airships may not carry units.
-  Great Drakes now have a 30 hand-to-hand attack strength, a 30 
   strength breath weapon, and a 10 defense.
-  Wizards lose 1/2 fame point per level of heroes slain in battle.
-  Maleus now has the spell of flame strike.
-  Rare and very rare fantastic units have had their defense 
   increased:
   Chaos Spawn:    6 DEF         Sky Drake      10 DEF
   Chimera:        5 DEF         Wraith:         6 DEF
   Efreet:         7 DEF         Death Knight:   8 DEF
   Great Drake:    9 DEF         Demon Lord:    10 DEF
   Angel:          7 DEF         Stone Giant:    8 DEF
   Arch Angel:    10 DEF         Gorgons:        7 DEF
   Storm Giant:    7 DEF         Beheemoth:      9 DEF
   Air Elemental:  5 DEF         Colossus       10 DEF
   Djinn:          8 DEF         Great Wyrm:    12 DEF

MOVEMENT:
-  Flyers may now use enchanted roads.
-  Teleport only costs 1 movement point in combat.
-  Pathfinding allows all units within the stack to move on land 
   squares as if they were roads.
-  Non-Corporal units can move on any terrain as a road.
-  Desert map squares cost one movement point to cross.

MISCELLANEOUS:
-  A left mouse click on any resource on the city view screen will 
   give a complete accounting and breakdown of resource production.
-  Trade Goods do not benefit from bonuses from any other source in 
   a city.
-  A conquering wizard may now chose to raze a city, totally 
   destroying the town and slaying all of its occupants. The razing 
   wizard then receives 10% of the original cost of all buildings 
   within the city, but loses 1 fame per size of the city, i.e. 
   1 fame for a hamlet, 2 for a village, 3 for a town, etc.
-  The default tax rate is 1 gold per townsfolk with a 20% unrest 
   rate.

---------------------------
Version 1.2 Chart Revisions
---------------------------

Building Chart:

                                RACES
Type         |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
--------------------------------------------------------
ALCHEMIST'S  | Y| Y| Y| Y| Y| N| Y| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
ANIMIST'S    | N| Y| Y| Y| N| N| N| Y| Y| N| N| Y| Y| Y|
--------------------------------------------------------
ARMORER'S    | Y| Y| Y| Y| Y| N| N| Y| Y| Y| N| Y| Y| Y| 
--------------------------------------------------------
ARMORY       | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
BANK         | N| Y| Y| Y| N| N| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
BARRACKS     | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
BUILDER'S    | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
CATHEDRAL    | N| Y| N| Y| N| N| Y| N| Y| N| N| Y| Y| Y|
--------------------------------------------------------
CITY WALLS   | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
FAN STABLE   | N| N| Y| N| N| N| N| Y| N| N| N| Y| Y| N|
--------------------------------------------------------
--------------------------------------------------------
TYPE         |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
--------------------------------------------------------
FARM MARKET  | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
FIGHTER'S G. | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
FORESTER'S   | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| Y|
--------------------------------------------------------
GRANARY      | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
HOUSING      | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
LIBRARY      | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
MARTIME G.   | Y| N| N| N| N| N| N| N| Y| N| N| N| Y| N|
--------------------------------------------------------
MARKET PLACE | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
MECHANICIAN'S| N| Y| Y| N| N| N| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
MERCHANT'S G.| N| N| Y| Y| N| N| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
--------------------------------------------------------
TYPE         |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
--------------------------------------------------------
MINER'S G.   | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| N|
--------------------------------------------------------
ORACLE       | N| Y| Y| Y| N| N| N| N| Y| N| N| Y| Y| N|
--------------------------------------------------------
PARTHENON    | Y| Y| Y| Y| N| N| N| N| Y| N| N| Y| Y| Y|
--------------------------------------------------------
SAGE'S G.    | Y| Y| Y| Y| Y| N| Y| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
SAWMILL      | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| Y|
--------------------------------------------------------
SHIP WRIGHTS | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| Y|
--------------------------------------------------------
SHIP YARD    | Y| N| Y| Y| N| Y| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
SHRINE       | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
SMITHY       | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
STABLE       | Y| Y| Y| Y| N| Y| N| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
--------------------------------------------------------
TYPE         |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
--------------------------------------------------------
TEMPLE       | Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| Y| Y| 
--------------------------------------------------------
TRADE GOODS  | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
--------------------------------------------------------
UNIVERSITY   | N| Y| Y| Y| N| N| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
WAR COLLEGE  | N| Y| Y| Y| N| N| N| Y| Y| N| N| Y| Y| N|
--------------------------------------------------------
WIZARD'S G.  | N| Y| Y| Y| N| N| N| Y| Y| N| N| N| Y| N|
--------------------------------------------------------

Units Chart:

                                RACES
TYPE          |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
---------------------------------------------------------
AIRSHIP       | N| N| N| Y| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
BESERKERS     | Y| N| N| N| N| N| N| N| N| N| N| N| N| N| 
---------------------------------------------------------
BOWMAN        | Y| Y| N| Y| N| Y| Y| N| Y| N| N| Y| Y| N|
---------------------------------------------------------
CAVALRY       | Y| N| Y| N| N| N| N| Y| Y| N| N| N| Y| N|
---------------------------------------------------------
CATAPULT      | N| Y| Y| N| N| N| N| Y| Y| N| N| Y| Y| N|
---------------------------------------------------------
CENTAURS      | N| Y| N| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
DOOM DRAKE    | N| N| N| Y| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
DRAGON TURTLE | N| N| N| N| N| N| N| N| N| N| Y| N| N| N|
---------------------------------------------------------
ELVEN LORDS   | N| N| N| N| N| N| N| Y| N| N| N| N| N| N|
---------------------------------------------------------
---------------------------------------------------------
TYPE          |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
---------------------------------------------------------
ENGINEERS     | N| Y| N| Y| Y| N| N| N| Y| Y| N| N| Y| N|
---------------------------------------------------------
GALLEY        | Y| N| Y| Y| N| Y| N| Y| Y| N| N| Y| Y| N|
---------------------------------------------------------
GOLEM         | N| N| N| N| Y| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
GRIFFINS      | N| N| N| N| N| N| N| N| N| N| N| Y| N| N|
---------------------------------------------------------
HALBERDS      | N| Y| Y| Y| Y| Y| N| Y| N| Y| Y| N| Y| Y|
---------------------------------------------------------
HAMMERHANDS   | N| N| N| N| Y| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
HORSEBOWMAN   | N| N| N| N| N| N| N| N| N| N| N| Y| N| N|
---------------------------------------------------------
JAVELINEERS   | N| N| N| N| N| N| N| N| N| N| Y| N| N| N|
---------------------------------------------------------
LONGBOWMAN    | N| N| N| N| N| N| N| Y| N| N| N| N| N| N|
---------------------------------------------------------
---------------------------------------------------------
TYPE          |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
---------------------------------------------------------
MAGICIANS     | N| Y| N| Y| N| N| N| Y| Y| N| N| N| Y| Y|
---------------------------------------------------------
MANTICORE     | N| Y| N| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
MINOTAURS     | N| Y| N| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
NIGHTBLADES   | N| N| Y| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
NIGHTMARES    | N| N| Y| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
PALADINS      | N| N| N| N| N| N| N| N| Y| N| N| N| N| N|
---------------------------------------------------------
PEGASI        | N| N| N| N| N| N| N| Y| N| N| N| N| N| N|
---------------------------------------------------------
PIKEMAN       | N| N| N| N| N| N| N| N| Y| N| N| Y| N| N|
---------------------------------------------------------
PRIEST        | N| Y| Y| N| N| N| N| N| Y| N| N| Y| N| N|
---------------------------------------------------------
---------------------------------------------------------
TYPE          |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
---------------------------------------------------------
RANGERS       | N| N| N| N| N| N| N| N| N| N| N| Y| N| N|
---------------------------------------------------------
SETTLERS      | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
---------------------------------------------------------
SHAMAN        | Y| N| N| Y| N| N| Y| N| N| N| Y| Y| Y| Y|
---------------------------------------------------------
SLINGERS      | N| N| N| N| N| N| Y| N| N| N| N| N| N| N|
---------------------------------------------------------
SPEARMAN      | Y| Y| Y| Y| N| Y| Y| Y| Y| Y| Y| Y| Y| Y|
---------------------------------------------------------
STAG BEETLE   | N| N| N| N| N| N| N| N| N| Y| N| N| N| N|
---------------------------------------------------------
STEAM CANNON  | N| N| N| N| Y| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
SWARDSMAN     | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| Y|
---------------------------------------------------------
TRIREME       | Y| Y| Y| Y| Y| Y| Y| Y| Y| Y| N| Y| Y| Y|
---------------------------------------------------------
---------------------------------------------------------
TYPE          |BA|BE|DE|DR|DW|GN|HF|HE|HM|KL|LZ|NO|OC|TR|
---------------------------------------------------------
WARLOCKS      | N| N| Y| N| N| N| N| N| N| N| N| N| N| N|
---------------------------------------------------------
WAR MAMMOTHS  | N| N| N| N| N| N| N| N| N| N| N| N| N| Y|
---------------------------------------------------------
WARSHIPS      | Y| N| N| N| N| N| N| N| Y| N| N| N| Y| N|
---------------------------------------------------------
WAR TROLLS    | N| N| N| N| N| N| N| N| N| N| N| N| N| Y|
---------------------------------------------------------
WYVERN RIDERS | N| N| N| N| N| N| N| N| N| N| N| N| Y| N|
---------------------------------------------------------

The following is a complete list of unrest modifiers according 
to a wizard's capitol race (ex. If you have a capitol race of
barbarians, you will have 1 additional unrest in a city of dwarves
you have conquered).

      BA    BE    DE    DR    DW    GN    HF 
BA:    0    +1    +1    +1    +1    +1    +1  
BE:   +1     0    +2    +2    +2     0    +1  
DE:   +1    +2     0    +2    +3    +2    +2  
DR:   +1    +2    +2     0    +2    +1    +1  
DW:   +1    +2    +3    +2     0    +1     0   
GN:   +1     0    +2    +1    +1     0     0   
HF:   +1    +1    +2    +1     0     0     0   
HE:   +1    +2    +4    +1    +3    +2     0   
HM:   +1    +1    +2    +1     0    +1     0   
KL:   +2    +2    +2    +2    +2    +2    +2  
LZ:   +1    +1    +2    +1    +1    +1    +1  
NO:    0    +1    +2    +1    +1    +1     0   
OC:    0    +1    +2    +1     0     0     0   
TR:   +1    +2    +3    +2     0     0    +1  

      HE    HM    KL    LZ    NO    OC    TR    
BA:   +1    +1    +2    +1     0     0    +1
BE:   +2    +1    +2    +1    +1    +1    +2
DE:   +4    +2    +2    +2    +2    +2    +3
DR:   +1    +1    +2    +1    +1    +1    +2
DW:   +3     0    +2    +1     0    +3    +4
GN:   +1    +1    +2    +1    +1     0     0
HF:    0     0    +2     0     0     0     0
HE:    0     0    +2    +1     0    +2    +3
HM:    0     0    +2    +1     0     0    +1
KL:   +2    +2    -2    +2    +2    +2    +2
LZ:   +1    +1    +2     0    +1    +1    +1
NO:    0     0    +2    +1     0     0    +1
OC:    0     0    +2    +1     0     0     0
TR:   +1    +1    +2    +1    +1     0     0

---------------------------------------------------------
Version 1.3.1 Corrections and Enhancements
---------------------------------------------------------

- You are awarded 5 fame points for defeating an enemy wizard. This is in
addition to fame points gained for defeating his fortress city. Note: you are
not notified of this award in the game.

- An asterisk that follows a hero's special ability indicates a super rating.


-  Non-corporeal units are unable to use the enchanted road bonus. The 
enchanted road bonus does not apply in combat.

- You will be rewarded with either one or two spells for banishing an enemy
wizard. However, both of you must have similar types of magic for this to
happen. If, for example, you have only death magic and your vanquished foe
has only life magic, don't expect any spell discoveries.

- Corruption now eliminates food production in the affected terrain.

- Volcanoes have a 2% chance to revert to mountains each turn (with a 5% 
chance of providing a mineral vein).

- The number of rebellions arising from Armageddon and Great Wasting have 
been substantially reduced (not entirely eliminated).

- A unit with an immunity to a special attack is no longer immune to all 
other attacks made by a unit that had that special attack.

- Units with magic immunity are no longer invulnerable to all fantastic
creatures.

- Djinns now have wind walking.

-We recommend that you not use saves from previous versions with 1.3.1. They 
might work fine but we cannot guarantee it.

- Playing with sound off should no longer crash the game in combat. 

- Armies of a banished wizard will now continue to follow their battleplan
instead of going onto the defensive as occurred in previous versions.

- Enemy wizards are now less apt to raze conquered cities.

- There is a limit of 1000 units allowed in the game. This means that if 
the other wizards have managed to recruit 950 units, you can at most 50. Any 
attempt to build another unit will cause a warning message to appear.

- A note on diplomacy. The stronger you get, the more difficult it will be 
to maintain good diplomatic relations with the other wizards and the more 
likely they will be to delcare war on you. They will not allow you grow
strong unchecked.

- Spell blast should now work properly against disjunction.

- The movement cost across destroyed outposts is 1.

- Units with mountainwalk capability move across grasslands at half rate.

- 

                * * * * * * * * * * * * 
                On-Line Service Support
                * * * * * * * * * * * *  
 
 MicroProse On-Line Support may be contacted on the
 following services:

        MPS*BBS*US              (410) 785-1841 
        CompuServe              support@microprose.com
        GEnie                   MicroProse
        Prodigy                 support@microprose.com
        America On-Line         MicroProse
        Internet                support@microprose.com
        Delphi                  support@microprose.com

 Updates, demos, and more may be found on the above services 
 as well as the following:

        World Wide Web          http://www.microprose.com
        FTP Site                ftp.microprose.com

----------------
Customer Support
----------------
If you are experiencing problems with Master of Magic, you can call
the MicroProse Customer Support Line at (410) 771-1151 weekdays from
9:00am -12:00pm and 1:30pm-7:00pm.


THANK YOU FOR PURCHASING MASTER OF MAGIC!

Distributed by MicroProse On-Line 1995
