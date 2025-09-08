from app import CardSorterApp

# This is in a separate file so that the AI helper stops
# deleting it when modifying the CardSorterApp itself.
csa = CardSorterApp()
csa.run()
