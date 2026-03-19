"""
Wave Investigation Engine - Replaces linear investigation with true wave architecture

This engine uses the WaveOrchestrator to conduct investigations where:
- Wave 1: Broad exploration from analytic question
- Wave N: Driven by previous wave's emergent questions
- Termination: When emergent questions converge

Based on correct dependency flow from correct_wave_example.json
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .wave_orchestrator import WaveOrchestrator
from .investigation_graph import InvestigationGraph
from .graph_aware_llm_coordinator import GraphAwareLLMCoordinator
from .realtime_insight_synthesizer import RealTimeInsightSynthesizer
from .search_executor import SearchExecutor
from .investigation_context import InvestigationContext
from .graph_visualizer import InvestigationGraphVisualizer
from .llm_client import LiteLLMClient

logger = logging.getLogger(__name__)

class WaveInvestigationEngine:
    """
    Wave-based investigation engine implementing true dependency architecture

    Replaces linear investigation_engine.py with wave cycles:
    AnalyticQuestion -> Wave1 -> EmergentQuestions -> Wave2 -> ... -> Convergence
    """

    def __init__(self):
        """Initialize wave investigation engine with all required components"""

        # Core components (reuse existing architecture)
        self.graph = InvestigationGraph()
        # Context will be initialized when investigation starts
        self.context = None

        # LLM coordinator and synthesizer will be initialized when investigation starts
        self.coordinator = None
        self.synthesizer = None

        # Search execution
        self.search_executor = SearchExecutor()

        # Wave orchestrator will be initialized when investigation starts
        self.wave_orchestrator = None

        # Graph visualizer for output
        self.visualizer = InvestigationGraphVisualizer()

        logger.info("Wave Investigation Engine initialized")

    def conduct_investigation(self, investigation_goal: str, max_waves: int = 5,
                            config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Conduct wave-based investigation

        Args:
            investigation_goal: The analytic question to investigate
            max_waves: Maximum number of waves (default: 5)
            config: Optional configuration overrides

        Returns:
            Investigation results in wave format matching correct_wave_example.json
        """
        logger.info(f"Starting wave investigation: '{investigation_goal}'")
        start_time = time.time()

        # Initialize context and components for this investigation
        self.context = InvestigationContext(
            analytic_question=investigation_goal,
            investigation_scope="Twitter investigation using wave architecture"
        )

        # Initialize LLM client
        llm_client = LiteLLMClient()

        self.coordinator = GraphAwareLLMCoordinator(
            llm_client=llm_client,
            graph=self.graph
        )

        self.synthesizer = RealTimeInsightSynthesizer(
            llm_client=llm_client,
            graph=self.graph,
            context=self.context
        )

        self.wave_orchestrator = WaveOrchestrator(
            graph=self.graph,
            coordinator=self.coordinator,
            synthesizer=self.synthesizer,
            search_executor=self.search_executor,
            context=self.context
        )

        try:
            # Apply configuration overrides
            if config:
                if 'max_waves' in config:
                    max_waves = config['max_waves']
                if 'convergence_threshold' in config:
                    self.wave_orchestrator.convergence_threshold = config['convergence_threshold']
                if 'question_reduction_threshold' in config:
                    self.wave_orchestrator.question_reduction_threshold = config['question_reduction_threshold']

            # Execute wave investigation
            investigation_result = self.wave_orchestrator.conduct_wave_investigation(
                investigation_goal=investigation_goal,
                max_waves=max_waves
            )

            # Add execution metadata
            investigation_result.update({
                "execution_time_seconds": time.time() - start_time,
                "engine_type": "wave_architecture",
                "timestamp": datetime.now().isoformat()
            })

            # Generate visualization
            self._generate_wave_visualization(investigation_result)

            # Log results summary
            self._log_investigation_summary(investigation_result)

            return investigation_result

        except Exception as e:
            logger.error(f"Wave investigation failed: {str(e)}")
            raise

    def _generate_wave_visualization(self, investigation_result: Dict[str, Any]) -> None:
        """Generate D3.js visualization showing wave dependencies"""
        try:
            investigation_id = investigation_result.get('investigation_id', 'unknown')

            # Save JSON output
            json_file = f"wave_investigation_{investigation_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(investigation_result, f, indent=2, ensure_ascii=False)

            # Generate graph visualization with wave context
            html_file = f"wave_investigation_{investigation_id}.html"

            # Create wave-specific visualization data
            wave_visualization_data = self._create_wave_visualization_data(investigation_result)

            # Use existing visualizer with hierarchical wave enhancements
            self.visualizer.save_wave_hierarchy_visualization(
                html_file,
                wave_data=wave_visualization_data,
                investigation_title=f"Wave Investigation: {investigation_result.get('investigation_goal', 'Unknown')}"
            )

            logger.info(f"Wave visualization saved: {html_file}")

        except Exception as e:
            logger.error(f"Failed to generate wave visualization: {str(e)}")

    def _create_wave_visualization_data(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization data showing investigation flow without wave nodes"""

        waves = investigation_result.get('waves', [])
        nodes = []
        edges = []

        # Create root analytic goal node
        investigation_goal = investigation_result.get('investigation_goal', 'Investigation')
        nodes.append({
            "id": "analytic_goal",
            "name": investigation_goal[:50] + "..." if len(investigation_goal) > 50 else investigation_goal,
            "type": "AnalyticGoal",
            "full_text": investigation_goal,
            "wave": 0
        })

        # Track previous questions for dependency chains
        previous_questions = []

        # Process each wave's computational cycle
        for wave in waves:
            wave_number = wave.get('wave_number', 0)

            # Create investigation questions (Wave 1) or use emergent questions (Wave 2+)
            if wave_number == 1:
                # Wave 1: Create investigation questions from analytic goal
                for i, driving_q in enumerate(wave.get('driving_questions', [])):
                    question_id = f"question_{wave_number}_{i}"
                    nodes.append({
                        "id": question_id,
                        "name": driving_q[:40] + "..." if len(driving_q) > 40 else driving_q,
                        "type": "InvestigationQuestion",
                        "full_text": driving_q,
                        "wave": wave_number
                    })

                    # Connect analytic goal to investigation questions
                    edges.append({
                        "source": "analytic_goal",
                        "target": question_id,
                        "type": "GENERATES"
                    })

                    previous_questions.append(question_id)
            else:
                # Wave 2+: Previous emergent questions become investigation questions
                # (These were already created in previous wave, just track them)
                pass

            # Create searches from questions
            current_questions = []
            if wave_number == 1:
                current_questions = [f"question_{wave_number}_{i}" for i in range(len(wave.get('driving_questions', [])))]
            else:
                # Use previous wave's emergent questions
                current_questions = previous_questions

            # Search nodes
            for i, search in enumerate(wave.get('searches_executed', [])):
                search_id = f"search_{wave_number}_{i}"
                nodes.append({
                    "id": search_id,
                    "name": f"{search.get('query', 'Unknown Query')[:30]}...",
                    "type": "Search",
                    "wave": wave_number,
                    "details": {
                        "query": search.get('query', ''),
                        "endpoint": search.get('endpoint', ''),
                        "results_count": search.get('results_count', 0)
                    }
                })

                # Connect questions to searches
                if i < len(current_questions):
                    edges.append({
                        "source": current_questions[i],
                        "target": search_id,
                        "type": "LEADS_TO"
                    })

            # DataPoint nodes (mock for now since we don't have detailed data)
            search_ids = [f"search_{wave_number}_{i}" for i in range(len(wave.get('searches_executed', [])))]
            for i, data_item in enumerate(wave.get('data_collected', [])[:5]):  # Limit to 5 for clarity
                data_id = f"data_{wave_number}_{i}"
                nodes.append({
                    "id": data_id,
                    "name": f"Data: {str(data_item)[:30]}..." if len(str(data_item)) > 30 else f"Data: {str(data_item)}",
                    "type": "DataPoint",
                    "wave": wave_number,
                    "full_text": str(data_item)
                })

                # Connect searches to data
                if search_ids:
                    source_search = search_ids[i % len(search_ids)]  # Cycle through searches
                    edges.append({
                        "source": source_search,
                        "target": data_id,
                        "type": "PRODUCES"
                    })

            # Insight nodes
            data_ids = [f"data_{wave_number}_{i}" for i in range(min(len(wave.get('data_collected', [])), 5))]
            for i, insight in enumerate(wave.get('insights_generated', [])):
                insight_id = f"insight_{wave_number}_{i}"
                nodes.append({
                    "id": insight_id,
                    "name": insight[:40] + "..." if len(insight) > 40 else insight,
                    "type": "Insight",
                    "wave": wave_number,
                    "full_text": insight
                })

                # Connect data to insights
                if data_ids:
                    for data_id in data_ids:
                        edges.append({
                            "source": data_id,
                            "target": insight_id,
                            "type": "SUPPORTS"
                        })

            # Emergent question nodes
            insight_ids = [f"insight_{wave_number}_{i}" for i in range(len(wave.get('insights_generated', [])))]
            current_emergent_questions = []
            for i, eq_question in enumerate(wave.get('emergent_questions', [])):
                eq_id = f"emergent_{wave_number}_{i}"
                nodes.append({
                    "id": eq_id,
                    "name": eq_question[:40] + "..." if len(eq_question) > 40 else eq_question,
                    "type": "EmergentQuestion",
                    "wave": wave_number,
                    "full_text": eq_question
                })

                # Connect insights to emergent questions
                if insight_ids:
                    source_insight = insight_ids[i % len(insight_ids)]  # Cycle through insights
                    edges.append({
                        "source": source_insight,
                        "target": eq_id,
                        "type": "GENERATES"
                    })

                current_emergent_questions.append(eq_id)

            # Set up for next wave
            previous_questions = current_emergent_questions

        return {
            "nodes": nodes,
            "edges": edges,
            "investigation_goal": investigation_result.get('investigation_goal', ''),
            "wave_count": len(waves),
            "dependency_chain": investigation_result.get('true_dependency_chain', {})
        }

    def _log_investigation_summary(self, investigation_result: Dict[str, Any]) -> None:
        """Log summary of wave investigation results"""

        waves = investigation_result.get('waves', [])
        metrics = investigation_result.get('wave_metrics', {})

        logger.info("=" * 60)
        logger.info("WAVE INVESTIGATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Goal: {investigation_result.get('investigation_goal', 'Unknown')}")
        logger.info(f"Waves Executed: {len(waves)}")
        logger.info(f"Total Searches: {metrics.get('total_searches', 0)}")
        logger.info(f"Total Insights: {metrics.get('total_insights', 0)}")
        logger.info(f"Total Emergent Questions: {metrics.get('total_emergent_questions', 0)}")
        logger.info(f"Final Satisfaction: {metrics.get('final_satisfaction', 0):.2f}")
        logger.info(f"Execution Time: {investigation_result.get('execution_time_seconds', 0):.1f}s")

        logger.info("\nWave Breakdown:")
        for wave in waves:
            logger.info(f"  Wave {wave.get('wave_number', 0)} ({wave.get('wave_type', '')}): "
                       f"{len(wave.get('searches_executed', []))} searches -> "
                       f"{len(wave.get('insights_generated', []))} insights -> "
                       f"{len(wave.get('emergent_questions', []))} questions")

        # Show dependency chain
        flow_demo = investigation_result.get('investigation_flow_demonstration', {})
        if flow_demo:
            logger.info("\nDependency Flow Example:")
            logger.info(f"  Wave 1 Insight: {flow_demo.get('wave_1_insight', '')[:80]}...")
            logger.info(f"  -> Emergent Question: {flow_demo.get('spawned_emergent_question', '')[:80]}...")
            logger.info(f"  -> Wave 2 Search: {flow_demo.get('becomes_wave_2_search', '')}")
            logger.info(f"  -> Wave 2 Data: {flow_demo.get('wave_2_data', '')[:80]}...")
            logger.info(f"  -> Wave 2 Insight: {flow_demo.get('wave_2_insight', '')[:80]}...")

        logger.info("=" * 60)

    def get_investigation_status(self) -> Dict[str, Any]:
        """Get current status of the investigation engine"""
        return {
            "engine_type": "wave_architecture",
            "components_initialized": all([
                self.graph is not None,
                self.search_executor is not None,
                self.visualizer is not None
            ]),
            "investigation_ready": all([
                self.coordinator is not None,
                self.synthesizer is not None,
                self.wave_orchestrator is not None,
                self.context is not None
            ]) if any([self.coordinator, self.synthesizer, self.wave_orchestrator, self.context]) else False,
            "graph_node_count": len(self.graph.nodes) if hasattr(self.graph, 'nodes') else 0,
            "context_state": str(self.context) if self.context else "Not initialized (will be created when investigation starts)"
        }