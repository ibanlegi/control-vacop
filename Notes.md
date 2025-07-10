# Notes - Explications

## Classe `MotorController` :
La classe `MotorController` est une implémentation du **Facade Pattern**, car elle fournit une interface simple et unifiée pour interagir avec différents sous-systèmes techniques (`SoloPy`, `GPIO`, configuration `CANopen`), tout en masquant leur complexité à l'utilisateur.

## Classe `myMotorController` :
La classe `myMotorController` est une implémentation du **Composite Pattern**, car elle regroupe deux objets `MotorController` et permet de les manipuler comme une seule unité logique (pour avancer, reculer, appliquer un couple, etc.). Elle masque également les détails de chaque moteur 
(direction inversée), 
jouant un rôle secondaire de **façade**, en fournissant une interface simplifiée pour des opérations sur plusieurs moteurs.
