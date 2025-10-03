"""
BLACK BOX Orchestrator - Thermal Monitoring
Proactive thermal management for Jetson Orin Nano 15W power mode
"""

import os
import time
import logging
import threading
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ThermalState(Enum):
    """Thermal states for the system"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    COOLDOWN = "cooldown"


@dataclass
class ThermalReading:
    """Single thermal reading"""
    temperature: float
    timestamp: float
    zone: str


class ThermalMonitor:
    """
    Monitors Jetson Orin Nano thermal zones and manages graceful degradation
    
    Thermal zones on Jetson:
    - /sys/devices/virtual/thermal/thermal_zone0/temp (CPU)
    - /sys/devices/virtual/thermal/thermal_zone1/temp (GPU)
    - /sys/devices/virtual/thermal/thermal_zone2/temp (SOC)
    """
    
    def __init__(
        self,
        warning_temp: float = 75.0,
        critical_temp: float = 85.0,
        cooldown_temp: float = 70.0,
        poll_interval: float = 2.0
    ):
        """
        Initialize thermal monitor
        
        Args:
            warning_temp: Temperature (°C) to enter warning state
            critical_temp: Temperature (°C) to enter critical state
            cooldown_temp: Temperature (°C) to exit cooldown
            poll_interval: Seconds between temperature checks
        """
        self.warning_temp = warning_temp
        self.critical_temp = critical_temp
        self.cooldown_temp = cooldown_temp
        self.poll_interval = poll_interval
        
        self.state = ThermalState.NORMAL
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Thermal zone paths
        self.thermal_zones = self._discover_thermal_zones()
        
        # Callbacks for state changes
        self.callbacks: Dict[ThermalState, list[Callable]] = {
            state: [] for state in ThermalState
        }
        
        # History
        self.readings: list[ThermalReading] = []
        self.max_history = 100
        
        logger.info(f"Thermal monitor initialized: warning={warning_temp}°C, critical={critical_temp}°C")
        logger.info(f"Discovered thermal zones: {list(self.thermal_zones.keys())}")
    
    def _discover_thermal_zones(self) -> Dict[str, str]:
        """
        Discover available thermal zones on the system
        
        Returns:
            Dictionary mapping zone names to file paths
        """
        zones = {}
        thermal_base = "/sys/class/thermal"
        
        # Check if thermal directory exists
        if not os.path.exists(thermal_base):
            logger.warning(f"Thermal directory not found: {thermal_base}")
            return zones
        
        # Scan for thermal zones
        for i in range(10):  # Check first 10 zones
            zone_path = f"{thermal_base}/thermal_zone{i}"
            temp_path = f"{zone_path}/temp"
            type_path = f"{zone_path}/type"
            
            if os.path.exists(temp_path):
                try:
                    # Read zone type
                    with open(type_path, 'r') as f:
                        zone_type = f.read().strip()
                    zones[zone_type] = temp_path
                except Exception as e:
                    logger.warning(f"Could not read thermal zone {i}: {e}")
        
        return zones
    
    def _read_temperature(self, zone_path: str) -> Optional[float]:
        """
        Read temperature from a thermal zone
        
        Args:
            zone_path: Path to thermal zone temp file
        
        Returns:
            Temperature in Celsius or None if read failed
        """
        try:
            with open(zone_path, 'r') as f:
                # Jetson reports temperature in millidegrees
                temp_millidegrees = int(f.read().strip())
                return temp_millidegrees / 1000.0
        except Exception as e:
            logger.debug(f"Failed to read temperature from {zone_path}: {e}")
            return None
    
    def get_current_temperatures(self) -> Dict[str, float]:
        """
        Get current temperatures from all zones
        
        Returns:
            Dictionary mapping zone names to temperatures
        """
        temps = {}
        for zone_name, zone_path in self.thermal_zones.items():
            temp = self._read_temperature(zone_path)
            if temp is not None:
                temps[zone_name] = temp
        return temps
    
    def get_max_temperature(self) -> Optional[float]:
        """
        Get maximum temperature across all zones
        
        Returns:
            Maximum temperature or None if no readings available
        """
        temps = self.get_current_temperatures()
        return max(temps.values()) if temps else None
    
    def _update_state(self, max_temp: float):
        """
        Update thermal state based on current temperature
        
        Args:
            max_temp: Maximum temperature across all zones
        """
        with self._lock:
            old_state = self.state
            
            # State machine
            if self.state == ThermalState.COOLDOWN:
                # Exit cooldown when temperature drops enough
                if max_temp < self.cooldown_temp:
                    self.state = ThermalState.NORMAL
                    logger.info(f"✓ Thermal cooldown complete: {max_temp:.1f}°C < {self.cooldown_temp}°C")
            
            elif max_temp >= self.critical_temp:
                self.state = ThermalState.CRITICAL
            
            elif max_temp >= self.warning_temp:
                self.state = ThermalState.WARNING
            
            else:
                self.state = ThermalState.NORMAL
            
            # Trigger callbacks if state changed
            if old_state != self.state:
                logger.warning(f"⚠ Thermal state changed: {old_state.value} → {self.state.value} ({max_temp:.1f}°C)")
                self._trigger_callbacks(self.state)
    
    def _trigger_callbacks(self, state: ThermalState):
        """
        Trigger all callbacks registered for a state
        
        Args:
            state: Thermal state that was entered
        """
        for callback in self.callbacks[state]:
            try:
                callback(state, self.get_current_temperatures())
            except Exception as e:
                logger.error(f"Thermal callback failed: {e}", exc_info=True)
    
    def register_callback(self, state: ThermalState, callback: Callable):
        """
        Register a callback for a thermal state
        
        Args:
            state: State to trigger callback
            callback: Function to call (receives state and temperatures dict)
        """
        self.callbacks[state].append(callback)
        logger.info(f"Registered thermal callback for {state.value} state")
    
    def _monitor_loop(self):
        """
        Main monitoring loop (runs in background thread)
        """
        logger.info("Thermal monitoring loop started")
        
        while self._running:
            try:
                # Read temperatures
                temps = self.get_current_temperatures()
                
                if temps:
                    max_temp = max(temps.values())
                    
                    # Store reading
                    reading = ThermalReading(
                        temperature=max_temp,
                        timestamp=time.time(),
                        zone=max(temps, key=temps.get)
                    )
                    self.readings.append(reading)
                    
                    # Trim history
                    if len(self.readings) > self.max_history:
                        self.readings = self.readings[-self.max_history:]
                    
                    # Update state
                    self._update_state(max_temp)
                    
                    # Log if elevated
                    if self.state != ThermalState.NORMAL:
                        logger.warning(
                            f"Thermal: {max_temp:.1f}°C (state: {self.state.value}) "
                            f"[zones: {', '.join(f'{k}={v:.1f}°C' for k, v in temps.items())}]"
                        )
                
                else:
                    logger.warning("No thermal readings available")
                
            except Exception as e:
                logger.error(f"Error in thermal monitoring loop: {e}", exc_info=True)
            
            # Sleep until next poll
            time.sleep(self.poll_interval)
        
        logger.info("Thermal monitoring loop stopped")
    
    def start(self):
        """Start thermal monitoring in background thread"""
        if self._running:
            logger.warning("Thermal monitor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("✓ Thermal monitoring started")
    
    def stop(self):
        """Stop thermal monitoring"""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Thermal monitoring stopped")
    
    def is_running(self) -> bool:
        """Check if thermal monitor is running"""
        return self._running
    
    def trigger_cooldown(self):
        """Manually trigger cooldown mode"""
        with self._lock:
            old_state = self.state
            self.state = ThermalState.COOLDOWN
            logger.warning(f"Manual cooldown triggered (was: {old_state.value})")
            self._trigger_callbacks(ThermalState.COOLDOWN)
    
    def get_status(self) -> Dict:
        """
        Get current thermal status
        
        Returns:
            Dictionary with thermal status information
        """
        temps = self.get_current_temperatures()
        max_temp = max(temps.values()) if temps else None
        
        return {
            "state": self.state.value,
            "temperatures": temps,
            "max_temperature": max_temp,
            "thresholds": {
                "warning": self.warning_temp,
                "critical": self.critical_temp,
                "cooldown": self.cooldown_temp
            },
            "is_throttling": self.state in [ThermalState.CRITICAL, ThermalState.COOLDOWN],
            "running": self._running
        }
    
    def should_throttle(self) -> bool:
        """
        Check if system should throttle due to thermal conditions
        
        Returns:
            True if system should reduce workload
        """
        return self.state in [ThermalState.CRITICAL, ThermalState.COOLDOWN]

