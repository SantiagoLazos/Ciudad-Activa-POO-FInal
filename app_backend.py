import csv
import os
import uuid #Para generar IDs únicos para los reportes
from typing import Dict, List #Para anotaciones de tipos en funciones y métodos
from dataclasses import dataclass, field #Para crear la clase Report como un Data Transfer Object (DTO) de forma sencilla
from fastapi import FastAPI, HTTPException #Para crear la API REST y manejar errores HTTP
from pydantic import BaseModel, EmailStr #Para validar los datos de entrada en las rutas de la API
import sqlite3 #Aunque inicialmente se usará CSV para persistencia, se importa sqlite3 por si se decide migrar a una base de datos ligera en el futuro._

#@dataclass para simplificar la creación de la clase Report, que representa un reporte de incidencia.
#Esta clase se utiliza como un DTO para transferir datos entre el backend y el frontend de manera estructurada.

@dataclass
class Report:
    #Clase que representa un reporte de incidencia.
    #Utiliza el patrón Data Transfer Object (DTO) mediante dataclass.
    id: str
    title: str
    description: str
    location: str
    image_path: str
    type_str: str  #'bache', 'basura', 'alumbrado', 'emergencia', 'otro'
    frequency: int = 0
    time_hours: float = 0.0
    priority: float = field(init=False, default=0.0)

    def __post_init__(self):
        #Calcula la prioridad inicial después de la inicialización.
        self.calculate_priority()

    def calculate_priority(self) -> float:
        #Calcula el score de prioridad basado en la fórmula:
        #Prioridad = (tipo * 0.4) + (frecuencia * 0.3) + (tiempo * 0.3)
        type_scores: dict[str, int] = {
            "bache": 70, 
            "basura": 50,
            "alumbrado": 60, 
            "emergencia": 90, 
            "otro": 40
        }
        
        #Obtiene el valor del tipo, por defecto 50 si el tipo no está en la lista.
        t_score = type_scores.get(self.type_str.lower(), 50)
        
        self.priority = (t_score * 0.4) + (self.frequency * 0.3) + (self.time_hours * 0.3)
        self.priority = round(self.priority, 2)
        return self.priority

class userManager:
    #Clase para manejar la autenticación de usuarios.
    #Utiliza un archivo CSV para almacenar las credenciales de los usuarios.
    
    def __init__(self, filename: str = "usuarios.csv") -> None:
        # Asegura que el archivo se guarde en el mismo directorio que este script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename: str = os.path.join(base_dir, filename)
        self.users: Dict[str, Dict] = {}
        self.load_users()

    def load_users(self) -> None:
        #Carga los usuarios desde el archivo CSV local.
        if not os.path.exists(self.filename):
            return
            
        try:
            with open(self.filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.users[row['correo']] = {
                        'contraseña': row['contraseña'],
                        'tipo': row['tipo']
                    }
        except Exception as e:
            print(f"Error al cargar los usuarios: {e}")

    def validate_user(self, email: str, password: str) -> bool:
        #Valida las credenciales del usuario.
        user = self.users.get(email)
        if user and user['contraseña'] == password:
            return True
        return False

    def register_user(self, email: str, password: str) -> bool:
        #Registra un nuevo usuario en el sistema.
        if email in self.users:
            return False  # Usuario ya existe
        self.users[email] = {
            'contraseña': password,
            'tipo': "ciudadano" #Haremos que por defecto todos los nuevos usuarios sean ciudadanos por seguridad, aunque se podría permitir elegir el tipo en una versión futura.
        }
        self.save_users()
        return True

class Backend:
    #Clase que maneja la lógica de negocio y la persistencia de datos (Model en el patrón MVC).
    #Se encarga de guardar y cargar la información desde un archivo CSV local.
    
    def __init__(self, filename: str = "inventario.csv") -> None:
        # Asegura que el archivo se guarde en el mismo directorio que este script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename: str = os.path.join(base_dir, filename)
        self.reports: List[Report] = []
        self.load_data()

    def load_data(self) -> None:
        #Carga los datos desde el archivo CSV local.
        if not os.path.exists(self.filename):
            return
            
        try:
            with open(self.filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Se recrea el reporte; __post_init__ recalculará la prioridad automáticamente.
                    report = Report(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        location=row['location'],
                        image_path=row['image_path'],
                        type_str=row['type_str'],
                        frequency=int(row['frequency']),
                        time_hours=float(row['time_hours'])
                    )
                    # Aseguramos de que se respete la prioridad guardada (aunque se recalcula si se actualiza)
                    report.priority = float(row['priority'])
                    self.reports.append(report)
        except Exception as e:
            print(f"Error al cargar los datos: {e}")

    def save_data(self) -> None:
        #Guarda la lista actual de reportes en el archivo CSV.
        fieldnames = [
            'id', 'title', 'description', 'location', 'image_path', 
            'type_str', 'frequency', 'time_hours', 'priority'
        ]
        try:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in self.reports:
                    writer.writerow({
                        'id': r.id,
                        'title': r.title,
                        'description': r.description,
                        'location': r.location,
                        'image_path': r.image_path,
                        'type_str': r.type_str,
                        'frequency': str(r.frequency),
                        'time_hours': str(r.time_hours),
                        'priority': str(r.priority)
                    })
        except Exception as e:
            print(f"Error al guardar los datos: {e}")

    def add_report(self, report: Report) -> None:
        #Añade un nuevo reporte a la lista, calcula su prioridad inicial
        #y guarda los cambios en persistencia.
        report.calculate_priority()
        self.reports.append(report)
        self.save_data()

    def update_report(self, report_id: str, updated_data: Dict) -> bool:
        #Actualiza un reporte existente buscándolo por su ID.
        #Retorna True si se actualizó correctamente, False en caso contrario.
        for r in self.reports:
            if r.id == report_id:
                if 'title' in updated_data: r.title = updated_data['title']
                if 'description' in updated_data: r.description = updated_data['description']
                if 'location' in updated_data: r.location = updated_data['location']
                if 'type_str' in updated_data: r.type_str = updated_data['type_str']
                if 'frequency' in updated_data: r.frequency = int(updated_data['frequency'])
                if 'time_hours' in updated_data: r.time_hours = float(updated_data['time_hours'])
                
                # Al actualizar valores clave, recalculamos la prioridad
                r.calculate_priority()
                self.save_data()
                return True
        return False

    def delete_report(self, report_id: str) -> bool:
        #Elimina un reporte de la lista utilizando list comprehension
        #y actualiza el archivo CSV. Retorna True si se eliminó, False si no se encontró el ID.
        initial_len = len(self.reports)
        self.reports = [r for r in self.reports if r.id != report_id]
        if len(self.reports) < initial_len:
            self.save_data()
            return True
        return False

    def search_reports(self, query: str) -> List[Report]:
        #Busca reportes cuyo título coincida con el texto de búsqueda.
        #Ignora mayúsculas y minúsculas.
        query = query.lower()
        return [r for r in self.reports if query in r.title.lower()]
    
    def get_all_reports(self) -> List[Report]:
        #Retorna todos los reportes actuales ordenados por prioridad de forma descendente.
        self.reports.sort(key=lambda x: x.priority, reverse=True)
        return self.reports
