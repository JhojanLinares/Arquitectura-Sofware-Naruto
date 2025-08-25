import json
import os
import pandas as pd
from abc import ABC, abstractmethod
from enum import Enum
import openpyxl


# enum y clases de dominio, lista a la izquierda 
#usa libreria unum, porque son rcurrentes

class RangoNinja(Enum):
    GENIN = "Genin"
    CHUNIN = "Chunin"
    JONIN = "Jonin"
    KAGE = "Kage"
    SANNIN = "Sannin"


class RangoMision(Enum):
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"


class Estadisticas:
    def __init__(self, ataque: int, defensa: int, chakra: int):
        self.ataque = ataque
        self.defensa = defensa
        self.chakra = chakra

    def entrenar(self, inc_ataque=0, inc_defensa=0, inc_chakra=0):
        self.ataque += inc_ataque
        self.defensa += inc_defensa
        self.chakra += inc_chakra


class Jutsu:
    def __init__(self, nombre: str, costo_chakra: int, efecto: str):
        self.nombre = nombre
        self.costo_chakra = costo_chakra
        self.efecto = efecto


class Aldea:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.ninjas: list[Ninja] = []

    def add_ninja(self, ninja: "Ninja"):
        self.ninjas.append(ninja)
        ninja.aldea = self


class Ninja:
    def __init__(self, nombre: str, rango: RangoNinja, estadisticas: Estadisticas):
        self.nombre = nombre
        self.rango = rango
        self.estadisticas = estadisticas
        self.jutsus: list[Jutsu] = []
        self.aldea: Aldea | None = None

    def entrenar(self, inc_ataque=5, inc_chakra=10, inc_defensa=0):
        self.estadisticas.entrenar(inc_ataque, inc_defensa, inc_chakra)

    def pelear(self, oponente: "Ninja") -> str:
        if self.estadisticas.ataque > oponente.estadisticas.defensa:
            return f"{self.nombre} gana contra {oponente.nombre}"
        else:
            return f"{oponente.nombre} resiste el ataque de {self.nombre}"

    def accept(self, visitor: "ExportVisitor"):
        return visitor.visit_ninja(self)


class Mision:
    def __init__(self, rango: RangoMision, recompensa: int, rango_requerido: RangoNinja):
        self.rango = rango
        self.recompensa = recompensa
        self.rango_requerido = rango_requerido

    def accept(self, visitor: "ExportVisitor"):
        return visitor.visit_mision(self)


#visitor para descargar 

class ExportVisitor(ABC):
    @abstractmethod
    def visit_ninja(self, ninja: Ninja):
        pass

    @abstractmethod
    def visit_mision(self, mision: Mision):
        pass


class JsonExportVisitor(ExportVisitor):
    def visit_ninja(self, ninja: Ninja):
        return {
            "nombre": ninja.nombre,
            "rango": ninja.rango.value,
            "aldea": ninja.aldea.nombre if ninja.aldea else None,
            "estadisticas": {
                "ataque": ninja.estadisticas.ataque,
                "defensa": ninja.estadisticas.defensa,
                "chakra": ninja.estadisticas.chakra
            },
            "jutsus": [{"nombre": j.nombre, "costo_chakra": j.costo_chakra, "efecto": j.efecto} for j in ninja.jutsus]
        }

    def visit_mision(self, mision: Mision):
        return {
            "rango": mision.rango.value,
            "recompensa": mision.recompensa,
            "rangoRequerido": mision.rango_requerido.value
        }


class XmlExportVisitor(ExportVisitor):
    def visit_ninja(self, ninja: Ninja):
        jutsus_xml = "".join([
            f"<jutsu><nombre>{j.nombre}</nombre><costo>{j.costo_chakra}</costo><efecto>{j.efecto}</efecto></jutsu>"
            for j in ninja.jutsus
        ])
        return (
            f"<ninja>"
            f"<nombre>{ninja.nombre}</nombre>"
            f"<rango>{ninja.rango.value}</rango>"
            f"<aldea>{ninja.aldea.nombre if ninja.aldea else ''}</aldea>"
            f"<estadisticas>"
            f"<ataque>{ninja.estadisticas.ataque}</ataque>"
            f"<defensa>{ninja.estadisticas.defensa}</defensa>"
            f"<chakra>{ninja.estadisticas.chakra}</chakra>"
            f"</estadisticas>"
            f"<jutsus>{jutsus_xml}</jutsus>"
            f"</ninja>"
        )

    def visit_mision(self, mision: Mision):
        return (
            f"<mision>"
            f"<rango>{mision.rango.value}</rango>"
            f"<recompensa>{mision.recompensa}</recompensa>"
            f"<rangoRequerido>{mision.rango_requerido.value}</rangoRequerido>"
            f"</mision>"
        )


class TextExportVisitor(ExportVisitor):
    def visit_ninja(self, ninja: Ninja):
        jutsus = ", ".join([j.nombre for j in ninja.jutsus]) or "Ninguno"
        return (
            f"Ninja: {ninja.nombre}\n"
            f"  Rango: {ninja.rango.value}\n"
            f"  Aldea: {ninja.aldea.nombre if ninja.aldea else 'Sin aldea'}\n"
            f"  Estadísticas -> Ataque: {ninja.estadisticas.ataque}, "
            f"Defensa: {ninja.estadisticas.defensa}, Chakra: {ninja.estadisticas.chakra}\n"
            f"  Jutsus: {jutsus}\n"
        )

    def visit_mision(self, mision: Mision):
        return (
            f"Misión rango {mision.rango.value}\n"
            f"  Recompensa: {mision.recompensa}\n"
            f"  Rango requerido: {mision.rango_requerido.value}\n"
        )


class ExcelExportVisitor(ExportVisitor):
    def __init__(self, filename="export.xlsx"):
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        self.filename = filename
        self.ninjas_data: list[dict] = []
        self.misiones_data: list[dict] = []

    def visit_ninja(self, ninja: Ninja):
        self.ninjas_data.append({
            "Nombre": ninja.nombre,
            "Rango": ninja.rango.value,
            "Aldea": ninja.aldea.nombre if ninja.aldea else None,
            "Ataque": ninja.estadisticas.ataque,
            "Defensa": ninja.estadisticas.defensa,
            "Chakra": ninja.estadisticas.chakra,
            "Jutsus": ", ".join([j.nombre for j in ninja.jutsus])
        })

    def visit_mision(self, mision: Mision):
        self.misiones_data.append({
            "Rango": mision.rango.value,
            "Recompensa": mision.recompensa,
            "Rango Requerido": mision.rango_requerido.value
        })

    def save(self):
        with pd.ExcelWriter(self.filename, engine="openpyxl") as writer:
            if self.ninjas_data:
                pd.DataFrame(self.ninjas_data).to_excel(writer, sheet_name="Ninjas", index=False)
            if self.misiones_data:
                pd.DataFrame(self.misiones_data).to_excel(writer, sheet_name="Misiones", index=False)
        return f"Datos exportados a {self.filename}"


#bider y factory

class NinjaBuilder:
    def __init__(self):
        self.nombre = None
        self.rango = RangoNinja.GENIN
        self.estadisticas = Estadisticas(10, 10, 50)
        self.jutsus: list[Jutsu] = []

    def with_nombre(self, nombre: str):
        self.nombre = nombre
        return self

    def with_rango(self, rango: RangoNinja):
        self.rango = rango
        return self

    def with_estadisticas(self, est: Estadisticas):
        self.estadisticas = est
        return self

    def with_jutsu(self, j: Jutsu):
        self.jutsus.append(j)
        return self

    def build(self) -> Ninja:
        ninja = Ninja(self.nombre, self.rango, self.estadisticas)
        for j in self.jutsus:
            ninja.jutsus.append(j)
        return ninja


class NinjaFactory(ABC):
    @abstractmethod
    def crear_ninja(self, nombre: str) -> Ninja:
        pass


class HojaFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.GENIN, Estadisticas(50, 40, 100))
        ninja.jutsus.append(Jutsu("Katon: Goukakyuu no Jutsu", 20, "Bola de fuego"))
        return ninja


class ArenaFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.CHUNIN, Estadisticas(60, 50, 120))
        ninja.jutsus.append(Jutsu("Sabaku Kyuu", 25, "Defensa y constricción de arena"))
        return ninja


class NieblaFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.GENIN, Estadisticas(55, 45, 90))
        ninja.jutsus.append(Jutsu("Suiton: Muro de Agua", 20, "Defensa acuática"))
        return ninja


class RocaFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.CHUNIN, Estadisticas(65, 60, 80))
        ninja.jutsus.append(Jutsu("Doton: Puño de Roca", 25, "Incremento de defensa y ataque"))
        return ninja


class NubeFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.JONIN, Estadisticas(70, 55, 110))
        ninja.jutsus.append(Jutsu("Raiton: Lanza Relámpago", 30, "Ataque eléctrico rápido"))
        return ninja


class SonidoFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.GENIN, Estadisticas(45, 40, 95))
        ninja.jutsus.append(Jutsu("Oto: Ondas Sonoras", 15, "Desorienta al enemigo"))
        return ninja


class LluviaFactory(NinjaFactory):
    def crear_ninja(self, nombre: str) -> Ninja:
        ninja = Ninja(nombre, RangoNinja.CHUNIN, Estadisticas(60, 50, 100))
        ninja.jutsus.append(Jutsu("Suiton: Lluvia Ácida", 25, "Daño progresivo"))
        return ninja


# lo que hace que esta vaina deje descargar -> lo que visitor forma 

def exportar_json(ninjas: list[Ninja], misiones: list[Mision], filename: str | None = None) -> str:
    visitor = JsonExportVisitor()
    data = {
        "ninjas": [n.accept(visitor) for n in ninjas],
        "misiones": [m.accept(visitor) for m in misiones]
    }
    texto = json.dumps(data, indent=2, ensure_ascii=False)
    
    if filename:
        # Añadir extensión .json si no la tiene
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Obtener la ruta absoluta
        full_path = os.path.abspath(filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(texto)
        return f"Datos JSON exportados a: {full_path}"
    return texto


def exportar_xml(ninjas: list[Ninja], misiones: list[Mision], filename: str | None = None) -> str:
    visitor = XmlExportVisitor()
    ninjas_xml = "".join([n.accept(visitor) for n in ninjas])
    misiones_xml = "".join([m.accept(visitor) for m in misiones])
    texto = f"<dataset><ninjas>{ninjas_xml}</ninjas><misiones>{misiones_xml}</misiones></dataset>"
    
    if filename:
        # Añadir extensión .xml si no la tiene
        if not filename.endswith('.xml'):
            filename += '.xml'
        
        # Obtener la ruta absoluta
        full_path = os.path.abspath(filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(texto)
        return f"Datos XML exportados a: {full_path}"
    return texto


def exportar_texto(ninjas: list[Ninja], misiones: list[Mision], filename: str | None = None) -> str:
    visitor = TextExportVisitor()
    partes = []
    if ninjas:
        partes.append("=== NINJAS ===\n")
        partes.extend([n.accept(visitor) for n in ninjas])
    if misiones:
        partes.append("=== MISIONES ===\n")
        partes.extend([m.accept(visitor) for m in misiones])
    texto = "\n".join(partes) if partes else "Sin datos para exportar."
    
    if filename:
        # Añadir extensión .txt si no la tiene
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Obtener la ruta absoluta
        full_path = os.path.abspath(filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(texto)
        return f"Datos de texto exportados a: {full_path}"
    return texto


def exportar_excel(ninjas: list[Ninja], misiones: list[Mision], filename: str = "export.xlsx") -> str:
    # Añadir extensión .xlsx si no la tiene
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
    
    # Obtener la ruta absoluta
    full_path = os.path.abspath(filename)
    
    exporter = ExcelExportVisitor(filename)
    for n in ninjas:
        n.accept(exporter)
    for m in misiones:
        m.accept(exporter)
    
    result = exporter.save()
    return f"{result}\n📍 Ruta completa: {full_path}"




def seleccionar_indice(opciones: list[str], prompt: str) -> int:
    for i, etiqueta in enumerate(opciones):
        print(f"{i}. {etiqueta}")
    while True:
        try:
            idx = int(input(prompt))
            if 0 <= idx < len(opciones):
                return idx
        except ValueError:
            pass
        print("Entrada no válida. Intenta de nuevo.")


def main():
    ninjas: list[Ninja] = []
    misiones: list[Mision] = []
    aldeas: list[Aldea] = []

    factories = {
        "hoja": HojaFactory(),
        "arena": ArenaFactory(),
        "niebla": NieblaFactory(),
        "roca": RocaFactory(),
        "nube": NubeFactory(),
        "sonido": SonidoFactory(),
        "lluvia": LluviaFactory(),
    }

    while True:
        print("\n=== MENÚ PRINCIPAL ===")
        print("1. crear aldea")
        print("2. crear ninja (builder o factory) y asignar a aldea")
        print("3. crear misión")
        print("4. entrenar ninja")
        print("5. pelear entre dos ninjas")
        print("6. exportar datos (Texto / JSON / XML / Excel)")
        print("7. listar aldeas y ninjas")
        print("0. Salir")

        opcion = input("elige una opción: ").strip()

        if opcion == "1":
            nombre = input("nombre de la aldea: ").strip()
            aldeas.append(Aldea(nombre))
            print(f"aldea {nombre} creada.")

        elif opcion == "2":
            if not aldeas:
                print("no hay aldeas. Crea una primero (opción 1).")
                continue

            print("1. crear ninja con builder")
            print("2. crear ninja con factory (aldea de origen)")
            subop = input("elige opción: ").strip()

            if subop == "1":
                nombre = input("nombre del ninja: ").strip()
                rango = RangoNinja[input("rango (Genin, Chunin, Jonin, Kage, Sannin): ").strip().upper()]
                ataque = int(input("ataque: ").strip())
                defensa = int(input("defensa: ").strip())
                chakra = int(input("chakra: ").strip())

                builder = NinjaBuilder()
                ninja = (builder
                         .with_nombre(nombre)
                         .with_rango(rango)
                         .with_estadisticas(Estadisticas(ataque, defensa, chakra))
                         .build())

                while True:
                    add_j = input("¿agregar jutsu? (s/n): ").strip().lower()
                    if add_j == "s":
                        jn = input("nombre del jutsu: ").strip()
                        jc = int(input("costo de chakra: ").strip())
                        je = input("efecto: ").strip()
                        ninja.jutsus.append(Jutsu(jn, jc, je))
                    else:
                        break

            elif subop == "2":
                nombre = input("nombre del ninja: ").strip()
                print("aldea de origen (hoja, arena, niebla, roca, nube, sonido, lluvia)")
                aldea_origen = input("aldea: ").strip().lower()
                factory = factories.get(aldea_origen)
                if not factory:
                    print("aldea no válida. Se creará un Genin básico por defecto.")
                    ninja = Ninja(nombre, RangoNinja.GENIN, Estadisticas(40, 40, 80))
                else:
                    ninja = factory.crear_ninja(nombre)
            else:
                print("opción no válida.")
                continue

            while True:
                aldea_asignar_nombre = input("elige la aldea a asignar por nombre: ").strip().lower()
                aldea_encontrada = next((a for a in aldeas if a.nombre.lower() == aldea_asignar_nombre), None)
                if aldea_encontrada:
                    aldea_encontrada.add_ninja(ninja)
                    ninjas.append(ninja)
                    print(f"ninja {ninja.nombre} creado y asignado a {aldea_encontrada.nombre}.")
                    break
                else:
                    print("aldea no encontrada. hazlo otra vez.")

        elif opcion == "3":
            rango = RangoMision[input("rango de la misión (D,C,B,A,S): ").strip().upper()]
            recompensa = int(input("recompensa: ").strip())
            rango_req = RangoNinja[input("rango requerido (Genin,Chunin,Jonin,Kage,Sannin): ").strip().upper()]
            mision = Mision(rango, recompensa, rango_req)
            misiones.append(mision)
            print(f"misión de rango {rango.value} creada.")

        elif opcion == "4":
            if not ninjas:
                print("no hay ninjas creados.")
                continue
            
            # Nuevo: Ahora permite buscar por nombre
            while True:
                print("ninjas disponibles para entrenar:")
                for n in ninjas:
                    print(f"- {n.nombre} ({n.rango.value})")

                ninja_entrenar_nombre = input("elige el ninja a entrenar por nombre: ").strip().lower()
                ninja_encontrado = next((n for n in ninjas if n.nombre.lower() == ninja_entrenar_nombre), None)
                
                if ninja_encontrado:
                    inc_atq = int(input("incremento de ataque: ").strip() or "0")
                    inc_def = int(input("incremento de defensa: ").strip() or "0")
                    inc_chk = int(input("incremento de chakra: ").strip() or "0")
                    ninja_encontrado.entrenar(inc_atq, inc_def, inc_chk)
                    est = ninja_encontrado.estadisticas
                    print(f"{ninja_encontrado.nombre} entrenó: Ataque={est.ataque}, Defensa={est.defensa}, Chakra={est.chakra}")
                    break
                else:
                    print("ninja no encontrado. repite nuevamente.")

        elif opcion == "5":
            if len(ninjas) < 2:
                print("necesitas al menos 2 ninjas.")
                continue

            # Nuevo: Ahora permite buscar por nombre
            while True:
                print("Elige los dos ninjas para el combate por nombre:")
                for n in ninjas:
                    print(f"- {n.nombre} ({n.rango.value})")
                
                ninja1_nombre = input("ninja 1: ").strip().lower()
                ninja2_nombre = input("ninja 2: ").strip().lower()

                ninja1 = next((n for n in ninjas if n.nombre.lower() == ninja1_nombre), None)
                ninja2 = next((n for n in ninjas if n.nombre.lower() == ninja2_nombre), None)

                if not ninja1 or not ninja2:
                    print("uno o ambos ninjas no fueron encontrados. repite el preceso.")
                    continue
                if ninja1 == ninja2:
                    print("debes elegir ninjas distintos.")
                    continue
                
                print(ninja1.pelear(ninja2))
                break

        elif opcion == "6":
            if not ninjas and not misiones:
                print("No hay datos para exportar.")
                continue

            print("Formatos disponibles: texto, json, xml, excel")
            fmt = input("Elige formato: ").strip().lower()

            if fmt == "texto":
                nombre = input("archivo de salida (vacío para mostrar en pantalla): ").strip()
                mensaje = exportar_texto(ninjas, misiones, filename=nombre if nombre else None)
                print(mensaje)
            elif fmt == "json":
                nombre = input("archivo de salida (vacío para mostrar en pantalla): ").strip()
                resultado = exportar_json(ninjas, misiones, filename=nombre if nombre else None)
                print(resultado if nombre else resultado)
            elif fmt == "xml":
                nombre = input("archivo de salida (vacío para mostrar en pantalla): ").strip()
                resultado = exportar_xml(ninjas, misiones, filename=nombre if nombre else None)
                print(resultado if nombre else resultado)
            elif fmt == "excel":
                nombre = input("archivo .xlsx (por defecto export.xlsx): ").strip() or "export.xlsx"
                print(exportar_excel(ninjas, misiones, filename=nombre))
            else:
                print("formato no reconocido.")

        elif opcion == "7":
            if not aldeas:
                print("no hay aldeas.")
                continue
            for a in aldeas:
                print(f"- {a.nombre}: {[n.nombre for n in a.ninjas] or 'Sin ninjas'}")

        elif opcion == "0":
            print("chao pescao...")
            break

        else:
            print("opción no válida.")


if __name__ == "__main__":
    main()