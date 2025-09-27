"""
Dummy ARGO data generator for testing the AI system.
Generates realistic oceanographic data for the Indian Ocean region.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import json

class ARGODataGenerator:
    def __init__(self, num_floats: int = 50, days_back: int = 365):
        self.num_floats = num_floats
        self.days_back = days_back
        self.floats_data = []
        self.profiles_data = []
        
        # Indian Ocean bounds
        self.min_lat, self.max_lat = -30, 30
        self.min_lon, self.max_lon = 20, 120
        
        # Oceanographic parameter ranges (realistic values)
        self.param_ranges = {
            'temperature': (0, 30),  # °C
            'salinity': (32, 37),    # PSU
            'pressure': (0, 2000),   # dbar
            'oxygen': (0, 300),      # μmol/kg
            'nitrate': (0, 50),      # μmol/kg
            'chlorophyll': (0, 5),   # mg/m³
            'backscatter': (0, 0.1), # m⁻¹
            'downwelling_irradiance': (0, 1000)  # μmol/m²/s
        }
    
    def generate_float_metadata(self) -> Dict[str, Any]:
        """Generate metadata for a single ARGO float."""
        float_id = f"ARGO_{random.randint(100000, 999999)}"
        
        # Random position in Indian Ocean
        lat = random.uniform(self.min_lat, self.max_lat)
        lon = random.uniform(self.min_lon, self.max_lon)
        
        # Deployment date (random within last 2 years)
        deployment_date = datetime.now() - timedelta(days=random.randint(30, 730))
        
        # Float status
        statuses = ['active', 'inactive', 'maintenance']
        status = random.choices(statuses, weights=[0.7, 0.2, 0.1])[0]
        
        # Platform type
        platform_types = ['PROVOR', 'APEX', 'SOLO', 'ARVOR']
        platform_type = random.choice(platform_types)
        
        return {
            'float_id': float_id,
            'platform_type': platform_type,
            'deployment_date': deployment_date,
            'latitude': lat,
            'longitude': lon,
            'status': status,
            'max_pressure': random.randint(1000, 2000),
            'cycle_time': random.randint(5, 10),  # days
            'institution': random.choice(['INCOIS', 'JAMSTEC', 'AOML', 'CSIO'])
        }
    
    def generate_profile_data(self, float_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate profile data for a float."""
        profiles = []
        deployment_date = float_metadata['deployment_date']
        cycle_time = float_metadata['cycle_time']
        
        # Generate profiles from deployment to now
        current_date = deployment_date
        profile_id = 0
        
        while current_date <= datetime.now():
            # Random position within ±0.5 degrees of deployment
            lat = float_metadata['latitude'] + random.uniform(-0.5, 0.5)
            lon = float_metadata['longitude'] + random.uniform(-0.5, 0.5)
            
            # Generate depth profile (0 to max_pressure)
            max_pressure = float_metadata['max_pressure']
            depths = np.linspace(0, max_pressure, random.randint(20, 100))
            
            profile_data = {
                'profile_id': f"{float_metadata['float_id']}_{profile_id:04d}",
                'float_id': float_metadata['float_id'],
                'timestamp': current_date,
                'latitude': lat,
                'longitude': lon,
                'depths': depths.tolist(),
                'parameters': {}
            }
            
            # Generate oceanographic parameters
            for param, (min_val, max_val) in self.param_ranges.items():
                # Create realistic depth profiles
                if param == 'temperature':
                    # Temperature decreases with depth
                    values = max_val - (depths / max_pressure) * (max_val - min_val) + np.random.normal(0, 1, len(depths))
                elif param == 'salinity':
                    # Salinity varies with depth
                    values = np.random.uniform(min_val, max_val, len(depths)) + np.sin(depths / 100) * 2
                elif param == 'pressure':
                    values = depths
                else:
                    # Other parameters with some depth variation
                    values = np.random.uniform(min_val, max_val, len(depths)) + np.random.normal(0, 0.1, len(depths))
                
                # Ensure values are within realistic bounds
                values = np.clip(values, min_val, max_val)
                profile_data['parameters'][param] = values.tolist()
            
            profiles.append(profile_data)
            profile_id += 1
            current_date += timedelta(days=cycle_time)
        
        return profiles
    
    def generate_all_data(self) -> tuple:
        """Generate complete dataset."""
        print(f"Generating data for {self.num_floats} ARGO floats...")
        
        for i in range(self.num_floats):
            float_metadata = self.generate_float_metadata()
            self.floats_data.append(float_metadata)
            
            profiles = self.generate_profile_data(float_metadata)
            self.profiles_data.extend(profiles)
            
            if (i + 1) % 10 == 0:
                print(f"Generated data for {i + 1} floats...")
        
        print(f"Data generation complete! Generated {len(self.floats_data)} floats and {len(self.profiles_data)} profiles.")
        return self.floats_data, self.profiles_data
    
    def save_to_csv(self, output_dir: str = "./data"):
        """Save generated data to CSV files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save float metadata
        floats_df = pd.DataFrame(self.floats_data)
        floats_df.to_csv(f"{output_dir}/argo_floats.csv", index=False)
        
        # Save profile data (flattened)
        profile_records = []
        for profile in self.profiles_data:
            base_record = {
                'profile_id': profile['profile_id'],
                'float_id': profile['float_id'],
                'timestamp': profile['timestamp'],
                'latitude': profile['latitude'],
                'longitude': profile['longitude']
            }
            
            # Add parameter data for each depth level
            for i, depth in enumerate(profile['depths']):
                record = base_record.copy()
                record['depth'] = depth
                for param, values in profile['parameters'].items():
                    record[param] = values[i]
                profile_records.append(record)
        
        profiles_df = pd.DataFrame(profile_records)
        profiles_df.to_csv(f"{output_dir}/argo_profiles.csv", index=False)
        
        print(f"Data saved to {output_dir}/")
        return floats_df, profiles_df
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of generated data."""
        return {
            'total_floats': len(self.floats_data),
            'total_profiles': len(self.profiles_data),
            'date_range': {
                'start': min(p['timestamp'] for p in self.profiles_data),
                'end': max(p['timestamp'] for p in self.profiles_data)
            },
            'geographic_bounds': {
                'min_lat': min(p['latitude'] for p in self.profiles_data),
                'max_lat': max(p['latitude'] for p in self.profiles_data),
                'min_lon': min(p['longitude'] for p in self.profiles_data),
                'max_lon': max(p['longitude'] for p in self.profiles_data)
            },
            'parameters': list(self.param_ranges.keys())
        }

if __name__ == "__main__":
    # Generate sample data
    generator = ARGODataGenerator(num_floats=20, days_back=180)
    floats_data, profiles_data = generator.generate_all_data()
    
    # Save to CSV
    floats_df, profiles_df = generator.save_to_csv()
    
    # Print summary
    stats = generator.get_summary_stats()
    print("\n=== Data Generation Summary ===")
    print(json.dumps(stats, indent=2, default=str))
