#!/usr/bin/env python3
"""
Генерация SVG-иллюстраций для разделов Руководства Renault Symbol.
Каждая функция создаёт SVG-файл в book/src/img/.

Требования: Python 3, Pillow
"""

import os
import textwrap

OUTPUT_DIR = "book/src/img"

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def svg_header(title, width=600, height=400):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" fill="#ffffff" rx="8"/>
  <text x="300" y="30" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="bold" fill="#333">{title}</text>
'''

def svg_footer():
    return '</svg>\n'

def rounded_rect(x, y, w, h, r=6, fill="#e8f0fe", stroke="#1565c0", stroke_w=2):
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"/>\n'

def label(text, x, y, size=12, color="#333", anchor="middle", bold=False):
    fw = "bold" if bold else "normal"
    return f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Inter, Arial, sans-serif" font-size="{size}" font-weight="{fw}" fill="{color}">{text}</text>\n'

def arrow(x1, y1, x2, y2, color="#666", width=2):
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" marker-end="url(#arrow)"/>\n'

def arrow_def():
    return '''  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#666"/>
    </marker>
  </defs>
'''

# === ГЕНЕРАТОРЫ ИЛЛЮСТРАЦИЙ ===

def gen_oil_circuit():
    """Система смазки двигателя — SVG"""
    w, h = 700, 450
    svg = svg_header("Система смазки двигателя K7J/K4J — схема циркуляции", w, h)
    svg += arrow_def()
    
    # Components
    comps = {
        "maslo": (250, 40, "Масляный\nподдон"),
        "nasos": (250, 130, "Масляный\nнасос"),
        "filter": (400, 130, "Масляный\nфильтр"),
        "golovka": (250, 250, "ГБЦ\n(распредвал,\nгидрокомпенсаторы)"),
        "blok": (400, 250, "Блок\n(коленвал,\nшатуны, поршни)"),
        "klapan": (550, 130, "Редукционный\nклапан"),
        "radiator": (100, 130, "Масляный\nрадиатор"),
    }
    
    for (cx, cy), (x, y) in zip(comps.values(), [(cx, cy) for cx, cy in comps.keys()]):
        pass  # we'll just use the actual positions
    
    # Draw boxes
    for (cx, cy), label_text in comps.items():
        wb, hb = 140, 65
        svg += rounded_rect(cx-70, cy-32, wb, hb, fill="#e3f2fd", stroke="#1565c0")
        svg += label(label_text, cx, cy-5, size=11, color="#1565c0")

    # Arrows for oil flow
    svg += arrow(250, 105, 250, 100)  # поддон → насос
    svg += arrow(320, 165, 390, 165)  # насос → фильтр
    svg += arrow(400, 195, 400, 210)  # фильтр ↓
    # Split to ГБЦ and блок
    svg += arrow(400, 230, 400, 240)
    svg += line(400, 240, 325, 240, "#666", 2)
    svg += arrow(325, 240, 250, 240)
    svg += arrow(400, 250, 400, 280)
    svg += arrow(400, 280, 400, 290)
    svg += line(400, 290, 325, 290, "#666", 2)
    svg += arrow(325, 290, 250, 290)
    # Return to sump
    svg += arrow(250, 315, 250, 380)
    svg += line(250, 380, 250, 390, "#666", 2)
    svg += arrow(250, 390, 250, 400)
    # Pressure relief
    svg += arrow(400, 165, 540, 165)  # filter → relief
    svg += arrow(550, 165, 550, 80, "#e65100")  # relief → sump (bypass)
    svg += label("Слив при\nизбытке\nдавления", 580, 100, size=10, color="#e65100")
    
    # Heat from radiator
    svg += arrow(100, 165, 100, 80, "#e65100")
    svg += label("Охлаждение\nмасла", 70, 100, size=10, color="#e65100")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/oil-circuit.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ oil-circuit.svg ({os.path.getsize(f'{OUTPUT_DIR}/oil-circuit.svg')} bytes)")


def line(x1, y1, x2, y2, color="#666", width=2):
    return f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>\n'


def gen_coolant_circuit():
    """Система охлаждения — SVG"""
    w, h = 700, 450
    svg = svg_header("Система охлаждения — циркуляция охлаждающей жидкости", w, h)
    svg += arrow_def()
    
    # Engine block
    svg += rounded_rect(250, 80, 160, 100, fill="#ffebee", stroke="#c62828")
    svg += label("Двигатель\n(рубашка охлаждения)", 330, 130, size=12, color="#c62828", bold=True)
    
    # Radiator
    svg += rounded_rect(250, 240, 160, 100, fill="#e3f2fd", stroke="#1565c0")
    svg += label("Радиатор", 330, 285, size=12, color="#1565c0", bold=True)
    svg += label("(верхний / нижний бачок)", 330, 305, size=10, color="#1565c0")
    
    # Thermostat
    svg += rounded_rect(460, 160, 100, 60, fill="#fff3e0", stroke="#e65100")
    svg += label("Термостат", 510, 180, size=11, color="#e65100", bold=True)
    svg += label("(открыт/закрыт)", 510, 198, size=10, color="#e65100")
    
    # Water pump
    svg += rounded_rect(460, 80, 100, 60, fill="#e8f5e9", stroke="#2e7d32")
    svg += label("Водяной\nнасос", 510, 105, size=11, color="#2e7d32", bold=True)
    
    # Expansion tank
    svg += rounded_rect(80, 80, 100, 60, fill="#fce4ec", stroke="#ad1457")
    svg += label("Расширительный\nбачок", 130, 105, size=10, color="#ad1457")
    
    # Heater core
    svg += rounded_rect(80, 240, 100, 60, fill="#f3e5f5", stroke="#6a1b9a")
    svg += label("Отопитель\nсалона", 130, 270, size=11, color="#6a1b9a", bold=True)
    
    # Arrows
    # Engine → Thermostat (hot coolant out)
    svg += arrow(410, 130, 455, 130)  # engine to thermostat (top)
    svg += label("горячий", 430, 120, size=9, color="#c62828")
    
    # Thermostat → Radiator (when open)
    svg += arrow(510, 220, 510, 238)  # thermostat down to...
    svg += line(510, 238, 410, 238, "#666", 2)
    svg += arrow(410, 238, 330, 238)  # ...radiator top
    svg += label("большой круг", 420, 232, size=9, color="#1565c0")
    
    # Radiator → Engine (coolant back)
    svg += arrow(330, 340, 330, 180)  # radiator bottom to engine bottom
    svg += label("охлаждённый", 300, 260, size=9, color="#1565c0")
    
    # Engine → Heater (hot for cabin)
    svg += arrow(250, 130, 185, 130)  # engine to heater
    svg += label("отопление", 220, 120, size=9, color="#6a1b9a")
    
    # Heater → Engine return
    svg += arrow(130, 300, 130, 340)
    svg += line(130, 340, 330, 340, "#666", 2)
    
    # Expansion tank connection
    svg += line(130, 140, 130, 190, "#ad1457", 1)
    svg += line(130, 190, 250, 190, "#ad1457", 1)
    svg += arrow(250, 190, 250, 183, "#ad1457", 1)
    svg += label("компенсация", 180, 185, size=9, color="#ad1457")
    
    # Bypass (small circle)
    svg += line(510, 160, 510, 145, "#e65100", 2)
    svg += arrow(510, 145, 460, 145, "#e65100", 2)
    svg += label("малый круг\n(термостат закрыт)", 580, 145, size=9, color="#e65100")
    
    # Legend
    svg += line(50, 390, 70, 390, "#666", 2)
    svg += label("поток жидкости", 80, 394, size=10, color="#666")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/coolant-circuit.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ coolant-circuit.svg ({os.path.getsize(f'{OUTPUT_DIR}/coolant-circuit.svg')} bytes)")


def gen_disc_brake():
    """Дисковый тормоз — SVG-иллюстрация"""
    w, h = 650, 400
    svg = svg_header("Дисковый тормоз — устройство и принцип работы", w, h)
    
    # Brake disc (rotor)
    svg += f'<circle cx="300" cy="200" r="100" fill="none" stroke="#666" stroke-width="8"/>'
    svg += f'<circle cx="300" cy="200" r="70" fill="none" stroke="#666" stroke-width="3" stroke-dasharray="8,4"/>'
    svg += f'<circle cx="300" cy="200" r="15" fill="#999" stroke="#666" stroke-width="2"/>'
    svg += label("Тормозной диск", 300, 90, size=11, color="#666")
    svg += label("(ротор)", 300, 105, size=10, color="#666")
    svg += label("ступица", 300, 210, size=9, color="#999")
    
    # Brake pads
    svg += f'<rect x="220" y="175" width="30" height="50" rx="3" fill="#e65100" stroke="#bf360c" stroke-width="2"/>'
    svg += label("Колодка", 235, 168, size=10, color="#bf360c")
    svg += label("(внутренняя)", 235, 160, size=9, color="#bf360c")
    
    svg += f'<rect x="350" y="175" width="30" height="50" rx="3" fill="#e65100" stroke="#bf360c" stroke-width="2"/>'
    svg += label("Колодка", 380, 168, size=10, color="#bf360c")
    svg += label("(наружная)", 380, 160, size=9, color="#bf360c")
    
    # Caliper
    svg += f'<path d="M 210 165 L 390 165 L 390 240 L 210 240 Z" fill="none" stroke="#1565c0" stroke-width="3" rx="5"/>'
    svg += f'<rect x="210" y="165" width="180" height="75" rx="5" fill="none" stroke="#1565c0" stroke-width="3"/>'
    svg += label("Суппорт", 300, 155, size=11, color="#1565c0", bold=True)
    
    # Piston
    svg += f'<rect x="260" y="178" width="20" height="44" rx="10" fill="#bbdefb" stroke="#1565c0" stroke-width="2"/>'
    svg += label("Поршень", 240, 245, size=9, color="#1565c0")
    svg += arrow(270, 222, 250, 222)  # piston pushes pad
    
    # Brake line
    svg += f'<path d="M 300 178 L 300 130 L 450 130" fill="none" stroke="#c62828" stroke-width="3"/>'
    svg += f'<circle cx="450" cy="130" r="12" fill="#c62828"/>'
    svg += label("Тормозная\nжидкость", 460, 120, size=10, color="#c62828")
    svg += label("(гидропривод)", 460, 155, size=9, color="#c62828")
    
    # Dimensions
    svg += line(190, 280, 190, 310, "#999", 1)
    svg += line(410, 280, 410, 310, "#999", 1)
    svg += line(190, 300, 410, 300, "#999", 1)
    svg += label("диаметр диска 259 мм", 300, 315, size=10, color="#999")
    
    # Legend
    svg += f'<rect x="40" y="340" width="12" height="12" fill="#e65100" stroke="#bf360c" rx="2"/>'
    svg += label("Колодка (накладка + металл)", 60, 351, size=10, color="#333")
    svg += f'<rect x="40" y="360" width="12" height="12" fill="none" stroke="#1565c0" rx="2" stroke-width="2"/>'
    svg += label("Суппорт (алюминиевый корпус)", 60, 371, size=10, color="#333")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/disc-brake.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ disc-brake.svg ({os.path.getsize(f'{OUTPUT_DIR}/disc-brake.svg')} bytes)")


def gen_suspension():
    """Передняя подвеска McPherson — SVG"""
    w, h = 500, 550
    svg = svg_header("Передняя подвеска — стойка McPherson (разрез)", w, h)
    
    # Upper mount
    svg += f'<rect x="200" y="30" width="100" height="25" rx="5" fill="#78909c" stroke="#546e7a" stroke-width="2"/>'
    svg += label("Верхняя опора\n(подушка стойки)", 250, 18, size=10, color="#546e7a")
    
    # Spring
    svg += f'<path d="M 215 55 L 200 80 L 300 100 L 200 140 L 300 160 L 200 200 L 300 220 L 215 250" fill="none" stroke="#e65100" stroke-width="4"/>'
    svg += label("Пружина", 310, 140, size=11, color="#e65100")
    
    # Shock absorber body
    svg += f'<rect x="240" y="55" width="20" height="220" rx="10" fill="#bbdefb" stroke="#1565c0" stroke-width="2"/>'
    svg += label("Амортизатор\n(газомасляный)", 270, 130, size=10, color="#1565c0")
    
    # Piston rod
    svg += f'<rect x="247" y="30" width="6" height="30" fill="#90a4ae" stroke="#546e7a" stroke-width="1"/>'
    svg += label("Шток", 260, 45, size=9, color="#546e7a")
    
    # Knuckle / steering arm
    svg += f'<rect x="230" y="270" width="40" height="50" rx="5" fill="#ffe0b2" stroke="#e65100" stroke-width="2"/>'
    svg += label("Поворотный\nкулак", 280, 285, size=10, color="#e65100")
    
    # Lower arm
    svg += f'<path d="M 230 320 L 80 370 L 80 380" fill="none" stroke="#1565c0" stroke-width="6" stroke-linecap="round"/>'
    svg += label("Нижний рычаг", 130, 365, size=10, color="#1565c0")
    
    # Ball joint
    svg += f'<circle cx="230" cy="320" r="8" fill="#c62828" stroke="#b71c1c" stroke-width="2"/>'
    svg += label("Шаровая\nопора", 200, 345, size=9, color="#c62828")
    
    # Stabilizer link
    svg += f'<line x1="300" y1="250" x2="350" y2="200" stroke="#6a1b9a" stroke-width="4" stroke-linecap="round"/>'
    svg += label("Стойка\nстабилизатора", 360, 215, size=9, color="#6a1b9a")
    
    # Stabilizer bar
    svg += f'<line x1="350" y1="200" x2="450" y2="180" stroke="#6a1b9a" stroke-width="6" stroke-linecap="round"/>'
    svg += label("Стабилизатор\nпоперечной\nустойчивости", 440, 175, size=9, color="#6a1b9a")
    
    # Drive shaft
    svg += f'<line x1="100" y1="260" x2="250" y2="290" stroke="#333" stroke-width="5" stroke-linecap="round"/>'
    svg += label("Приводной вал\n(ШРУС)", 100, 250, size=9, color="#333")
    
    # Wheel hub
    svg += f'<rect x="230" y="295" width="15" height="15" rx="3" fill="#666" stroke="#444" stroke-width="1"/>'
    svg += label("Ступица", 250, 310, size=9, color="#666")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/suspension-mcpherson.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ suspension-mcpherson.svg ({os.path.getsize(f'{OUTPUT_DIR}/suspension-mcpherson.svg')} bytes)")


def gen_battery():
    """АКБ — обслуживание и параметры"""
    w, h = 600, 350
    svg = svg_header("Аккумуляторная батарея — устройство и обслуживание", w, h)
    
    # Battery body
    svg += f'<rect x="200" y="60" width="200" height="160" rx="15" fill="#e8eaf6" stroke="#283593" stroke-width="3"/>'
    svg += f'<rect x="210" y="70" width="180" height="30" rx="5" fill="#c5cae9" stroke="#283593" stroke-width="1"/>'
    
    # Terminals
    svg += f'<rect x="255" y="40" width="10" height="25" rx="3" fill="#c62828"/>'
    svg += label("+", 260, 35, size=14, color="#c62828", bold=True)
    svg += label("Клемма (+)", 260, 25, size=10, color="#c62828")
    
    svg += f'<rect x="335" y="40" width="10" height="25" rx="3" fill="#333"/>'
    svg += label("−", 340, 35, size=14, color="#333", bold=True)
    svg += label("Клемма (−)", 340, 25, size=10, color="#333")
    
    # Cells
    for i, (x_pos, label_txt) in enumerate([(220, "−"), (260, "−"), (300, "+"), (340, "+"), (370, "+")]):
        fill = "#e3f2fd" if i < 3 else "#fce4ec"
        svg += f'<rect x="{x_pos}" y="115" width="30" height="90" rx="4" fill="{fill}" stroke="#90a4ae" stroke-width="1"/>'
    
    svg += label("Элементы (банки)", 300, 110, size=9, color="#546e7a")
    svg += label("2.1 В каждый", 300, 220, size=9, color="#546e7a")
    svg += label("Итого: 6 × 2.1 В = 12.6 В", 300, 240, size=11, color="#283593", bold=True)
    
    # Electrolyte level
    svg += f'<rect x="220" y="145" width="25" height="60" rx="2" fill="#bbdefb" opacity="0.5"/>'
    svg += label("Электролит\n(H₂SO₄)", 210, 170, size=9, color="#1565c0")
    
    # Plates
    svg += f'<rect x="225" y="155" width="3" height="40" fill="#999"/>'
    svg += f'<rect x="237" y="155" width="3" height="40" fill="#999"/>'
    svg += label("пластины\n(Pb / PbO₂)", 245, 175, size=8, color="#666")
    
    # Specs
    specs = [
        "Напряжение: 12 В",
        "Ёмкость: 45–70 А·ч",
        "Пусковой ток: 300–600 А",
        "Полярность: прямая / обратная",
        "Срок службы: 4–5 лет",
    ]
    for j, spec in enumerate(specs):
        svg += label(spec, 60, 280 + j*18, size=10, color="#333")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/battery.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ battery.svg ({os.path.getsize(f'{OUTPUT_DIR}/battery.svg')} bytes)")


def gen_timing_belt():
    """Ремень ГРМ — схема"""
    w, h = 600, 400
    svg = svg_header("Привод ГРМ — схема ремня и шкивов", w, h)
    
    # Crankshaft pulley (bottom)
    svg += f'<circle cx="300" cy="310" r="45" fill="none" stroke="#333" stroke-width="5"/>'
    svg += f'<circle cx="300" cy="310" r="15" fill="#666" stroke="#333" stroke-width="2"/>'
    svg += f'<rect x="285" y="340" width="30" height="20" rx="3" fill="#78909c" stroke="#546e7a" stroke-width="1"/>'
    svg += label("Шкив\nколенвала", 300, 275, size=10, color="#333", bold=True)
    svg += label("(звёздочка)", 300, 290, size=9, color="#666")
    
    # Camshaft pulley (top, offset)
    svg += f'<circle cx="300" cy="90" r="35" fill="none" stroke="#1565c0" stroke-width="5"/>'
    svg += f'<circle cx="300" cy="90" r="12" fill="#1565c0" stroke="#0d47a1" stroke-width="2"/>'
    svg += label("Шкив\nраспредвала", 300, 50, size=10, color="#1565c0", bold=True)
    
    # Belt
    svg += f'<path d="M 300 45 L 300 265" stroke="#e65100" stroke-width="4" stroke-dasharray="8,4" fill="none"/>'
    svg += label("Ремень ГРМ", 310, 160, size=10, color="#e65100", bold=True)
    
    # Tensioner
    svg += f'<circle cx="380" cy="200" r="15" fill="none" stroke="#6a1b9a" stroke-width="3"/>'
    svg += f'<circle cx="380" cy="200" r="5" fill="#6a1b9a"/>'
    svg += label("Натяжной\nролик", 400, 195, size=9, color="#6a1b9a")
    
    # Water pump pulley
    svg += f'<circle cx="400" cy="310" r="20" fill="none" stroke="#2e7d32" stroke-width="3"/>'
    svg += label("Шкив\nпомпы", 430, 310, size=9, color="#2e7d32")
    
    # Belt path outline
    svg += f'<path d="M 300 55 L 300 265 L 350 310 L 380 215 L 380 185 L 300 55" fill="none" stroke="#e65100" stroke-width="2" opacity="0.3"/>'
    
    # Timing marks
    svg += f'<line x1="300" y1="90" x2="300" y2="55" stroke="#c62828" stroke-width="2"/>'
    svg += f'<line x1="300" y1="310" x2="300" y2="265" stroke="#c62828" stroke-width="2"/>'
    svg += label("▲ метки", 260, 55, size=9, color="#c62828")
    svg += label("▲ метки", 260, 265, size=9, color="#c62828")
    
    # Order
    svg += label("Порядок замены ГРМ:", 60, 360, size=10, color="#333", bold=True)
    svg += label("1. Снять ремень навесных агрегатов", 60, 375, size=9, color="#666")
    svg += label("2. Зафиксировать коленвал и распредвал", 60, 388, size=9, color="#666")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/timing-belt.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ timing-belt.svg ({os.path.getsize(f'{OUTPUT_DIR}/timing-belt.svg')} bytes)")


def gen_noise_isolation():
    """Шумоизоляция — зоны обработки"""
    w, h = 650, 400
    svg = svg_header("Шумоизоляция Symbol — рекомендуемые зоны обработки", w, h)
    
    # Car silhouette (simplified top view)
    body = "M 100 200 Q 150 120 250 120 L 400 120 L 500 170 L 520 260 L 450 320 L 150 320 L 100 260 Z"
    svg += f'<path d="{body}" fill="#f5f5f5" stroke="#999" stroke-width="2"/>'
    
    # Zone 1: Floor
    svg += f'<path d="M 130 280 L 440 280 L 420 200 L 150 200 Z" fill="#e3f2fd" stroke="#1565c0" stroke-width="2" opacity="0.6"/>'
    svg += label("Зона 1: Пол\n(вибро- + шумоизоляция)", 285, 240, size=10, color="#1565c0", bold=True)
    
    # Zone 2: Doors
    svg += f'<rect x="100" y="170" width="20" height="100" rx="3" fill="#fff3e0" stroke="#e65100" stroke-width="2"/>'
    svg += f'<rect x="480" y="180" width="20" height="90" rx="3" fill="#fff3e0" stroke="#e65100" stroke-width="2"/>'
    svg += label("Зона 2: Двери\n(вибро + герметизация)", 510, 175, size=9, color="#e65100")
    
    # Zone 3: Trunk
    svg += f'<ellipse cx="490" cy="280" rx="35" ry="30" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2" opacity="0.6"/>'
    svg += label("Зона 3: Багажник\n(арки + ниша)", 530, 280, size=9, color="#2e7d32")
    
    # Zone 4: Hood
    svg += f'<ellipse cx="250" cy="140" rx="50" ry="15" fill="#fce4ec" stroke="#c62828" stroke-width="2" opacity="0.5"/>'
    svg += label("Зона 4: Капот\n(теплоизол)", 200, 130, size=9, color="#c62828")
    
    # Labels for car parts
    svg += label("Капот", 250, 110, size=8, color="#666")
    svg += label("Салон", 285, 200, size=8, color="#666")
    svg += label("Багажник", 500, 250, size=8, color="#666")
    
    # Materials legend
    materials = [
        ("✅ Вибропласт Silver (2 мм)", "#1565c0"),
        ("✅ Сплэн (4–8 мм)", "#c62828"),
        ("✅ Бипласт (5–10 мм)", "#e65100"),
        ("✅ Вибротон (2.5–4 мм)", "#2e7d32"),
    ]
    for j, (mat, color) in enumerate(materials):
        svg += f'<rect x="60" y="340" width="10" height="10" fill="{color}" rx="2"/>'
        svg += label(mat, 78, 349, size=9, color=color)
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/noise-isolation-zones.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ noise-isolation-zones.svg ({os.path.getsize(f'{OUTPUT_DIR}/noise-isolation-zones.svg')} bytes)")


def gen_tools():
    """Инструменты для ремонта — SVG"""
    w, h = 650, 350
    svg = svg_header("Инструменты для ремонта Renault Symbol", w, h)
    
    tools = [
        (60,  60, "🔧", "Набор ключей\n(рожковые, торцевые)"),
        (160, 60, "🔩", "Головки + трещотка\n1/2\" и 1/4\""),
        (260, 60, "🔨", "Молоток + оправки\n(для сайлентблоков)"),
        (360, 60, "🛞", "Динамометрический\nключ (10–210 Н·м)"),
        (460, 60, "🔌", "Мультиметр\n(тестер, прозвонка)"),
        (110, 180, "🛢️", "Съёмники: фильтра,\nшаровых, стопорных"),
        (210, 180, "⚡", "Стартовый провод\n(прикуривание)"),
        (310, 180, "🛞", "Домкрат + подставки\n(безопасность)"),
        (410, 180, "🧰", "Отвёртки: шлиц,\nкрест, Torx"),
    ]
    
    for x, y, icon, desc in tools:
        svg += label(icon, x+25, y+10, size=24, anchor="middle")
        svg += label(f"  {desc}", x+50, y-5, size=9, color="#333")
    
    svg += label("Рекомендуемый минимум для самостоятельного ремонта", 300, 330, size=10, color="#666", anchor="middle")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/tools.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ tools.svg ({os.path.getsize(f'{OUTPUT_DIR}/tools.svg')} bytes)")


def gen_alternator():
    """Генератор — схема"""
    w, h = 550, 350
    svg = svg_header("Генератор Valeo — устройство", w, h)
    
    # Main body
    svg += f'<rect x="150" y="80" width="250" height="150" rx="20" fill="#e8eaf6" stroke="#283593" stroke-width="3"/>'
    
    # Stator
    svg += f'<circle cx="275" cy="155" r="50" fill="none" stroke="#1565c0" stroke-width="4"/>'
    svg += label("Статор\n(обмотка)", 275, 155, size=10, color="#1565c0", bold=True)
    
    # Rotor
    svg += f'<circle cx="275" cy="155" r="20" fill="#e65100" stroke="#bf360c" stroke-width="2"/>'
    svg += label("Ротор\n(магнит)", 275, 120, size=9, color="#bf360c")
    
    # Pulley
    svg += f'<circle cx="120" cy="155" r="25" fill="none" stroke="#666" stroke-width="4"/>'
    svg += f'<circle cx="120" cy="155" r="8" fill="#666"/>'
    svg += label("Шкив\nпривода", 120, 130, size=9, color="#666")
    
    # Belt
    svg += f'<line x1="145" y1="155" x2="200" y2="155" stroke="#e65100" stroke-width="3"/>'
    svg += label("Ремень", 170, 170, size=8, color="#e65100")
    
    # Regulator
    svg += f'<rect x="350" y="90" width="40" height="50" rx="5" fill="#fff3e0" stroke="#e65100" stroke-width="2"/>'
    svg += label("Реле-\nрегулятор", 370, 85, size=9, color="#e65100")
    
    # Diode bridge
    svg += f'<rect x="350" y="150" width="40" height="50" rx="5" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>'
    svg += label("Диодный\nмост", 370, 148, size=9, color="#c62828")
    
    # Output terminal
    svg += f'<rect x="380" y="180" width="40" height="10" rx="3" fill="#c62828"/>'
    svg += label("B+ (выход)", 420, 190, size=9, color="#c62828")
    
    # Output arrow
    svg += arrow(390, 185, 430, 185, "#c62828", 2)
    
    # Specs
    svg += label("Характеристики:", 60, 280, size=10, color="#333", bold=True)
    svg += label("• Напряжение: 12 В", 60, 298, size=9, color="#666")
    svg += label("• Ток: 80–120 А", 60, 313, size=9, color="#666")
    svg += label("• Мощность: 1.0–1.5 кВт", 60, 328, size=9, color="#666")
    
    svg += svg_footer()
    
    with open(f"{OUTPUT_DIR}/alternator.svg", "w") as f:
        f.write(svg)
    print(f"  ✅ alternator.svg ({os.path.getsize(f'{OUTPUT_DIR}/alternator.svg')} bytes)")


# === MAIN ===

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    generators = [
        gen_oil_circuit,
        gen_coolant_circuit,
        gen_disc_brake,
        gen_suspension,
        gen_battery,
        gen_timing_belt,
        gen_noise_isolation,
        gen_tools,
        gen_alternator,
    ]
    
    for gen in generators:
        gen()
    
    total = sum(os.path.getsize(f"{OUTPUT_DIR}/{f}") for f in os.listdir(OUTPUT_DIR) if f.endswith('.svg'))
    print(f"\n📊 Всего SVG иллюстраций: {len(generators)}, общий размер: {total//1024} KB")


if __name__ == "__main__":
    main()
