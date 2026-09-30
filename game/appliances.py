from dataclasses import dataclass


@dataclass(frozen=True)
class Appliance:
    key: str
    name: str
    icon: str
    watts: int
    target_hours: int  # hours the household "wants" to run it for full comfort
    comfort_weight: float  # how much the household cares about this appliance
    essential: bool = False  # essential appliances must reach target_hours


APPLIANCES = [
    Appliance("fridge", "Refrigerator", "🧊", 60, 24, 2.0, essential=True),
    Appliance("cooktop", "Electric cooktop", "🍳", 1200, 2, 2.5, essential=True),
    Appliance("ac", "Air conditioner", "❄️", 1500, 8, 3.0),
    Appliance("fan", "Ceiling fan", "🌀", 60, 10, 1.0),
    Appliance("lights", "Lights", "💡", 60, 6, 2.0),
    Appliance("tv", "Television", "📺", 120, 4, 1.5),
    Appliance("computer", "Computer", "💻", 100, 5, 1.5),
    Appliance("washer", "Washing machine", "🧺", 500, 1, 1.5),
    Appliance("heater", "Water heater", "🚿", 2000, 1, 2.0),
    Appliance("iron", "Iron", "👕", 1000, 1, 1.0),
]
