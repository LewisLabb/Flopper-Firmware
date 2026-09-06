# flopper

Firmware Flipper Zero, fork de [Momentum](https://github.com/Next-Flip/Momentum-Firmware).

**flopper n'ajoute pas une centième fonction à ton Flipper. Il rend enfin évident, rapide et agréable tout ce qu'il sait déjà faire.**

Dès le déballage, une installation guidée te met en route en deux minutes : firmware, apps curées, thème et réglages, sans jamais ouvrir un dossier. L'écran d'accueil se comprend en trois secondes. Taper un mot de passe n'est plus un supplice — clavier prédictif, pré-saisies, ou ton téléphone en relais. Tes apps s'installent et se mettent à jour en Wi-Fi, sans PC. Tu branches une carte externe, elle se présente toute seule.

Et parce que la confiance compte autant que la puissance : flopper sait dans quelle région tu es et te dit clairement ce qui est permis chez toi. Puissant par défaut, responsable par défaut.

Ce n'est pas « la dernière mise à jour de l'histoire ». C'est la version qui, enfin, se sent finie — celle qu'on garde.

## Ce que ce projet ne fait pas

**Il n'écrit pas son propre flasheur.** Il produit du firmware ; l'installer reste le travail du Web Updater de Momentum, de qFlipper, ou de `./fbt flash_usb_full` en développement. C'est l'opération la plus risquée pour le matériel, et elle est déjà résolue ailleurs.

**Il ne réinvente pas la radio.** Momentum possède déjà presque toutes les fonctions.

## Construire

```bash
./fbt                   # construire le firmware
./fbt flash_usb_full    # flasher l'appareil connecte
./fbt lint              # verifier le style C

ufbt                    # construire une application autonome
ufbt launch             # la construire et la lancer sur l'appareil connecte
```

## Où regarder

| Fichier | Contenu |
| --- | --- |
| `FEUILLE-DE-ROUTE.md` | La vision, les six piliers, l'ordre des chantiers |
| `AGENTS.md` | Les règles de travail, les garde-fous matériels et réglementaires |
| `taches/` | Les fiches de tâche et leurs journaux de revue |

## Avertissement

Ce firmware donne accès à des fonctions radio dont l'usage est encadré par la loi, et cet encadrement varie d'un pays à l'autre. Les profils régionaux sont conservateurs par défaut ; les déverrouiller est un choix explicite, et la responsabilité de la loi locale reste celle de l'utilisateur. La réception est en général moins encadrée que l'émission.
