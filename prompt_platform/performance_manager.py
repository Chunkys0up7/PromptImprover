"""
Performance optimization and caching management for the Prompt Platform.

This module provides centralized performance optimization including:
- Optimized data loading with pagination
- Async operation management with timeouts
- Resource caching and management
- Performance metrics tracking
"""
import asyncio
import time
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class PerformanceManager:
    """Centralized performance optimization and caching management"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.operation_times = {}
    
    @staticmethod
    @st.cache_data(ttl=300, show_spinner="Loading prompts...")
    def load_prompts_optimized(page: int = 0, page_size: int = 20) -> Dict[str, Any]:
        """Optimized prompt loading with pagination and caching"""
        start_time = time.time()
        
        try:
            # Get paginated prompts
            prompts = st.session_state.db.get_all_prompts()  # For now, keep existing method
            
            # Calculate pagination
            total_count = len(prompts)
            start_idx = page * page_size
            end_idx = start_idx + page_size
            paginated_prompts = prompts[start_idx:end_idx]
            
            load_time = time.time() - start_time
            logger.info(f"Loaded {len(paginated_prompts)} prompts in {load_time:.2f}s")
            
            return {
                'prompts': paginated_prompts,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'load_time': load_time
            }
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return {
                'prompts': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'load_time': 0,
                'error': str(e)
            }
    
    @staticmethod
    @st.cache_resource
    def get_heavy_resources():
        """Cache expensive resource initialization"""
        logger.info("Initializing heavy resources...")
        return {
            'prompt_generator': st.session_state.prompt_generator,
            'version_manager': st.session_state.version_manager,
        }
    
    def run_async_operation(self, coro, timeout: int = 30, operation_name: str = "async_operation"):
        """Run async operations with timeout and proper error handling"""
        start_time = time.time()
        
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Operation {operation_name} timed out after {timeout} seconds")
                return None
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                return None
            finally:
                loop.close()
        
        try:
            future = self.executor.submit(run_in_thread)
            result = future.result(timeout=timeout + 5)  # Extra buffer for thread overhead
            
            operation_time = time.time() - start_time
            self.operation_times[operation_name] = operation_time
            logger.info(f"Operation {operation_name} completed in {operation_time:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"Failed to execute {operation_name}: {e}")
            return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'operation_times': self.operation_times.copy(),
            'average_operation_time': sum(self.operation_times.values()) / len(self.operation_times) if self.operation_times else 0,
            'total_operations': len(self.operation_times),
            'cache_hits': getattr(st.cache_data, '_cache_info', lambda: {'hits': 0, 'misses': 0})(),
        }
    
    def clear_cache(self):
        """Clear all caches"""
        st.cache_data.clear()
        st.cache_resource.clear()
        logger.info("Cleared all caches")
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

class ProgressTracker:
    """Track and display progress for long-running operations"""
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.progress_bar = None
        self.status_text = None
    
    def __enter__(self):
        """Context manager entry"""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        if self.status_text:
            self.status_text.empty()
    
    def update(self, step_description: str, step_increment: int = 1):
        """Update progress with description"""
        self.current_step += step_increment
        progress = min(self.current_step / self.total_steps, 1.0)
        
        if self.progress_bar:
            self.progress_bar.progress(progress)
        if self.status_text:
            self.status_text.text(f"{self.operation_name}: {step_description}")
        
        logger.debug(f"Progress: {self.current_step}/{self.total_steps} - {step_description}")
    
    def complete(self, final_message: str = "Complete!"):
        """Mark operation as complete"""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        if self.status_text:
            self.status_text.text(f"{self.operation_name}: {final_message}")
        logger.info(f"{self.operation_name} completed: {final_message}")

def show_performance_metrics():
    """Display performance metrics in the UI"""
    if 'performance_manager' in st.session_state:
        metrics = st.session_state.performance_manager.get_performance_metrics()
        
        st.subheader("📊 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Operations", metrics['total_operations'])
        
        with col2:
            avg_time = metrics['average_operation_time']
            st.metric("Avg Operation Time", f"{avg_time:.2f}s")
        
        with col3:
            cache_info = metrics['cache_hits']
            if isinstance(cache_info, dict):
                hit_rate = cache_info.get('hits', 0) / max(cache_info.get('hits', 0) + cache_info.get('misses', 1), 1) * 100
                st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
        
        # Show recent operation times
        if metrics['operation_times']:
            st.subheader("Recent Operations")
            for operation, time_taken in list(metrics['operation_times'].items())[-5:]:
                st.text(f"• {operation}: {time_taken:.2f}s") 