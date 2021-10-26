# METHODE d'écriture de mon code

Après de nombreux essais, je pense que le code exécutable par l'OT-2 doit être sous forme de Jupyter-notebook (JNB). 
En effet, seule cette méthode permet une interaction entre le code et l'utilisateur.

Problème : les fichiers de jupyter-notebook ne sont pas faciles à suivre avec git.

Je vais donc conserver mon script sous format d'un fichier python dans lequel on définit la fonction run().

Le nom du fichier */py est de type "monorun_xxx.py". Le nom du JNB sera "xxx".

J'ai créé un modèle de JNB, verrouillé, dont on commence par en faire une copie.

Les premières cellules contiennent des commandes pour créer le context de l'OT dans le JNB.

Une cellule reçoit tout le code que l'on pourrait mettre dans un module.
Une autre reçoit la fonction run(). 
La cellule suivante est pour exécuter le run().
La suivante permet de voir le log de l'objet ctx.

En entête une variable permet d'indiquer si l'utilisateur utilise un vrai OT ou bien utilise le simulateur.

Comment faire évoluer le code : 
 - modifier le programme monorun acvec Pycharm. 
 - on peut l'exécuter en tant que fichier python.
 - on peut l'exécuter avec opentrons_simulate.
 - le sauver (importer)
 - ouvrir le JNB
 - activer la ligne %load.
 - activer les autres cellules du JNB.