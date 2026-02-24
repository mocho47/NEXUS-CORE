import gc
import logging
import psutil
import os
from datetime import datetime

class PerformanceManager:
    def __init__(self, config_manager, system_monitor):
        self.config = config_manager
        self.monitor = system_monitor
        self.logger = logging.getLogger("NexusV2.PerformanceManager")

    def check_and_optimize(self):
        """Check system status and trigger optimization if needed."""
        metrics = self.monitor.get_system_metrics()
        if not metrics:
            return

        max_mem = float(self.config.get_config('max_memory_usage', 80))
        
        if metrics['memory_usage'] > max_mem:
            self.logger.warning(f"Memory usage ({metrics['memory_usage']}%) exceeds threshold ({max_mem}%). Optimizing...")
            return self.optimize_memory()
        
        return {"status": "nominal", "message": "System within limits"}

    def optimize_memory(self):
        """Perform memory optimization tasks."""
        initial_mem = psutil.virtual_memory().percent
        
        # 1. Force Garbage Collection
        gc_counts = gc.get_count()
        freed = gc.collect()
        
        # 2. Optional: Clear internal caches if any (placeholder)
        # self.cache.clear()
        
        final_mem = psutil.virtual_memory().percent
        saved = initial_mem - final_mem
        
        result = {
            "status": "optimized",
            "freed_objects": freed,
            "memory_saved_percent": round(saved, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Optimization complete. Freed {freed} objects. Memory: {initial_mem}% -> {final_mem}%")
        return result
