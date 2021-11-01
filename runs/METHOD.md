# METHODE d'écriture de mon code

Après de nombreux essais, je pense que le code exécutable par l'OT-2 doit être sous forme de Jupyter-notebook (JNB). 
En effet, seule cette méthode permet une interaction entre le code et l'utilisateur.

Mon problème est que les fichiers de type jupyter-notebook ne sont pas faciles à suivre avec git tout au moins avec la 
version libre de PyCharm.  

Je vais donc conserver mon script sous format d'un fichier python dans lequel on définit la fonction run().

Le nom du fichier */py est de type "xxx_monorun.py". Le nom du JNB sera "xxx".

J'ai créé un modèle de JNB, verrouillé, dont on commence par en faire une copie.

Les premières cellules contiennent des commandes pour créer le context de l'OT dans le JNB.

Une cellule tout le fichier "xxx_monorun.py" grâce au mot magique `%load`. 
La cellule suivante est pour exécuter le run().
La suivante permet de voir le log de l'objet ctx.

Prévision : une variable en entête permet d'indiquer si l'utilisateur utilise un vrai OT ou bien utilise le simulateur.
