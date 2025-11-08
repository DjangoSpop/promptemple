"""
Ask-Me Prompt Builder Service

This service implements the Ask-Me prompt engineering process using LangChain
with two main components:
- Planner: Decides what questions to ask next
- Composer: Builds the final prompt from the complete spec
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings
from django.core.cache import cache
from asgiref.sync import sync_to_async

from .models import AskMeSession, AskMeQuestion
from .orchestration.langchain_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

@dataclass
class QuestionSpec:
    """Specification for a single question"""
    qid: str
    title: str
    help_text: str
    kind: str
    options: List[str]
    variable: str
    required: bool
    suggested: str

@dataclass
class PlannerResult:
    """Result from the Planner service"""
    questions: List[QuestionSpec]
    good_enough_to_run: bool
    metadata: Dict[str, Any]

@dataclass
class ComposerResult:
    """Result from the Composer service"""
    prompt: str
    metadata: Dict[str, Any]

class AskMeService:
    """
    Main service for the Ask-Me prompt builder system.

    Implements the two-stage process:
    1. Planner: Analyzes intent + current spec → generates questions
    2. Composer: Takes complete spec → generates final prompt
    """

    def __init__(self):
        """Initialize the service with LangChain chains"""
        # TEMPORARY: Force fallback mode for development
        force_fallback = True  # Set to False when LangChain templates are fixed

        if force_fallback:
            logger.info("AskMe service: Using fallback mode for development")
            self.orchestrator = None
            self.llm = None
            self.planner_chain = None
            self.composer_chain = None
            return

        try:
            self.orchestrator = get_orchestrator()
            self.llm = self.orchestrator.llm

            # Create the specialized chains
            self.planner_chain = self._create_planner_chain()
            self.composer_chain = self._create_composer_chain()

            logger.info("AskMe service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AskMe service: {e}")
            # Set up fallback mode
            self.orchestrator = None
            self.llm = None
            self.planner_chain = None
            self.composer_chain = None
            logger.warning("AskMe service running in fallback mode")

    def _create_planner_chain(self):
        """Create the Planner LangChain chain"""

        # System prompt for the Planner
        system_prompt = """You are the Planner for an Ask-Me prompt builder.

OBJECTIVE
Given INTENT and current partially-filled SPEC, determine the next 0–3 most valuable questions needed to produce a professional final prompt.

RULES
- Ask only for missing or ambiguous variables.
- Prefer structured fields. Map each question to a SPEC variable.
- Keep each question resolvable with a short answer.
- If minimal viable prompt is met, return an empty list.

INPUTS
- intent: free text (user's goal)
- spec_json: current PromptSpec as JSON with fields:
  goal, audience, tone, style, context, constraints, inputs

OUTPUT (strict JSON):
Return a JSON object with "questions_json" array containing question objects.
Each question should have: qid, title, help_text, kind, options, variable, required, suggested fields.
Do not include any other text - only the JSON response.

DEVELOPER HINTS:
- If goal is missing: ask for it first.
- If audience is missing: ask "Who will read/use this?"
- If tone/style missing: offer 4–6 choices (e.g., professional, friendly, persuasive, concise).
- If constraints/context unclear: ask 1 focused question each.
- For domain-specific variables (e.g., "email_subject", "app_features"), propose short_text or multichoice with common options.

Examples of question kinds:
- "short_text" for simple inputs
- "choice" for multiple options with an options array
- "long_text" for detailed descriptions
- "boolean" for yes/no questions

IMPORTANT: Return only valid JSON. No additional text or commentary."""

        # Human prompt template
        human_template = """Intent: {intent}

Current Spec: {spec_json}

Generate the next questions needed to complete this prompt specification."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template)
        ])

        return prompt | self.llm | StrOutputParser()

    def _create_composer_chain(self):
        """Create the Composer LangChain chain"""

        # System prompt for the Composer
        system_prompt = """You are the Composer. Create a polished, production-ready prompt from the completed PromptSpec.

REQUIREMENTS
- Output a single prompt string that:
  1) States the Goal clearly.
  2) Adapts to the Audience.
  3) Honors Tone & Style.
  4) Incorporates Context and Constraints.
  5) Injects Inputs as named variables if needed.
- Keep it concise, actionable, and deterministic.
- No meta commentary. No placeholders left unresolved unless intentionally provided as variables.

INPUTS
- spec_json with fields: goal, audience, tone, style, context, constraints, inputs

OUTPUT
- Return ONLY the final prompt text (no JSON, no headings).

FORMAT TEMPLATE:

Goal:
- [Use the goal from spec]

Audience:
- [Use the audience from spec]

Tone & Style:
- Tone: [Use the tone from spec]
- Style: [Use the style from spec]

Context:
- [Use the context from spec]

Constraints:
- [Use the constraints from spec]

Required Inputs:
[List any inputs from spec]

Instruction:
Generate the requested output adhering strictly to Constraints,
tailored to Audience and Tone.
Use any Required Inputs if present. Avoid boilerplate explanations."""

        # Human prompt template
        human_template = """Spec: {spec_json}

Create the final prompt based on this specification."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template)
        ])

        return prompt | self.llm | StrOutputParser()

    async def plan_questions(self, intent: str, spec: Dict[str, Any]) -> PlannerResult:
        """
        Use the Planner to determine what questions to ask next.

        Args:
            intent: User's original intent/goal
            spec: Current prompt specification

        Returns:
            PlannerResult with questions to ask
        """
        # Check if we're in fallback mode
        if self.planner_chain is None:
            logger.warning("Using fallback planning - LangChain not available")
            fallback_questions = self._generate_fallback_questions(spec)
            return PlannerResult(
                questions=fallback_questions,
                good_enough_to_run=len(fallback_questions) == 0,
                metadata={"fallback": True, "reason": "LangChain not available"}
            )

        try:
            # Prepare input for the planner
            input_data = {
                "intent": intent,
                "spec_json": json.dumps(spec, indent=2)
            }

            logger.info(f"Planning questions for intent: {intent[:100]}...")

            # Run the planner chain
            result = await self.planner_chain.ainvoke(input_data)

            # Parse the JSON result
            parsed_result = self._parse_planner_result(result)

            # Check if we have enough for a good prompt
            good_enough = len(parsed_result.questions) == 0 or self._is_spec_sufficient(spec)

            return PlannerResult(
                questions=parsed_result.questions,
                good_enough_to_run=good_enough,
                metadata={
                    "intent": intent,
                    "spec_completeness": self._calculate_spec_completeness(spec),
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Failed to plan questions: {e}")

            # Fallback: ask for basic fields if missing
            fallback_questions = self._generate_fallback_questions(spec)

            return PlannerResult(
                questions=fallback_questions,
                good_enough_to_run=len(fallback_questions) == 0,
                metadata={"error": str(e), "fallback": True}
            )

    async def compose_prompt(self, spec: Dict[str, Any]) -> ComposerResult:
        """
        Use the Composer to generate the final prompt.

        Args:
            spec: Complete prompt specification

        Returns:
            ComposerResult with the final prompt
        """
        # Check if we're in fallback mode
        if self.composer_chain is None:
            logger.warning("Using fallback composition - LangChain not available")
            fallback_prompt = self._generate_fallback_prompt(spec)
            return ComposerResult(
                prompt=fallback_prompt,
                metadata={"fallback": True, "reason": "LangChain not available"}
            )

        try:
            # Prepare input for the composer
            input_data = {
                "spec_json": json.dumps(spec, indent=2)
            }

            logger.info("Composing final prompt...")

            # Run the composer chain
            result = await self.composer_chain.ainvoke(input_data)

            return ComposerResult(
                prompt=result.strip(),
                metadata={
                    "spec": spec,
                    "timestamp": datetime.now().isoformat(),
                    "spec_completeness": self._calculate_spec_completeness(spec)
                }
            )

        except Exception as e:
            logger.error(f"Failed to compose prompt: {e}")

            # Fallback: create a basic prompt
            fallback_prompt = self._generate_fallback_prompt(spec)

            return ComposerResult(
                prompt=fallback_prompt,
                metadata={"error": str(e), "fallback": True}
            )

    def _parse_planner_result(self, result: str) -> PlannerResult:
        """Parse the JSON result from the Planner"""
        try:
            # Clean the result and extract JSON
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:-3]
            elif result.startswith("```"):
                result = result[3:-3]

            data = json.loads(result)
            questions_data = data.get("questions_json", [])

            questions = []
            for i, q_data in enumerate(questions_data):
                question = QuestionSpec(
                    qid=q_data.get("qid", f"q_{i+1}"),
                    title=q_data.get("title", ""),
                    help_text=q_data.get("help_text", ""),
                    kind=q_data.get("kind", "short_text"),
                    options=q_data.get("options", []),
                    variable=q_data.get("variable", f"var_{i+1}"),
                    required=q_data.get("required", True),
                    suggested=q_data.get("suggested", "")
                )
                questions.append(question)

            return PlannerResult(
                questions=questions,
                good_enough_to_run=len(questions) == 0,
                metadata={"parsed_successfully": True}
            )

        except Exception as e:
            logger.error(f"Failed to parse planner result: {e}")
            return PlannerResult(
                questions=[],
                good_enough_to_run=True,
                metadata={"parse_error": str(e)}
            )

    def _generate_fallback_questions(self, spec: Dict[str, Any]) -> List[QuestionSpec]:
        """Generate fallback questions when AI planning fails"""
        questions = []

        # Always ask for goal first if missing
        if not spec.get("goal"):
            questions.append(QuestionSpec(
                qid="goal_q1",
                title="What is the main goal or purpose?",
                help_text="Describe what you want to achieve",
                kind="long_text",
                options=[],
                variable="goal",
                required=True,
                suggested=""
            ))

        # Ask for audience if missing
        if not spec.get("audience"):
            questions.append(QuestionSpec(
                qid="audience_q2",
                title="Who is your target audience?",
                help_text="Who will read or use this content?",
                kind="choice",
                options=["General public", "Business executives", "Technical team", "Students", "Marketing team", "Clients/Customers"],
                variable="audience",
                required=True,
                suggested=""
            ))

        # Ask for tone if missing
        if not spec.get("tone"):
            questions.append(QuestionSpec(
                qid="tone_q3",
                title="What tone should this have?",
                help_text="Choose the appropriate tone for your content",
                kind="choice",
                options=["Professional", "Friendly", "Persuasive", "Concise", "Formal", "Casual"],
                variable="tone",
                required=True,
                suggested=""
            ))

        # Ask for style if missing and we have other fields
        if not spec.get("style") and len(questions) < 3:
            questions.append(QuestionSpec(
                qid="style_q4",
                title="What style should this follow?",
                help_text="Choose the writing or presentation style",
                kind="choice",
                options=["Clear and direct", "Detailed and comprehensive", "Brief and concise", "Creative and engaging", "Technical and precise"],
                variable="style",
                required=False,
                suggested=""
            ))

        # Ask for context if we have room
        if not spec.get("context") and len(questions) < 2:
            questions.append(QuestionSpec(
                qid="context_q5",
                title="Any important context or background?",
                help_text="Provide relevant context that should be considered",
                kind="long_text",
                options=[],
                variable="context",
                required=False,
                suggested=""
            ))

        return questions[:3]  # Limit to 3 questions max

    def _generate_fallback_prompt(self, spec: Dict[str, Any]) -> str:
        """Generate a fallback prompt when AI composition fails"""
        goal = spec.get("goal", "Complete the requested task")
        audience = spec.get("audience", "")
        tone = spec.get("tone", "")
        style = spec.get("style", "")
        context = spec.get("context", "")
        constraints = spec.get("constraints", "")

        # Build the prompt step by step
        prompt_parts = []

        # Main goal
        prompt_parts.append(f"Goal: {goal}")

        # Audience specification
        if audience:
            prompt_parts.append(f"Target Audience: {audience}")

        # Tone and style
        tone_style_parts = []
        if tone:
            tone_style_parts.append(f"Tone: {tone}")
        if style:
            tone_style_parts.append(f"Style: {style}")

        if tone_style_parts:
            prompt_parts.append("Requirements:")
            for part in tone_style_parts:
                prompt_parts.append(f"- {part}")

        # Context
        if context:
            prompt_parts.append(f"Context: {context}")

        # Constraints
        if constraints:
            prompt_parts.append(f"Constraints: {constraints}")

        # Instructions
        instructions = "Instructions:"
        if audience:
            instructions += f" Create content tailored for {audience}."
        if tone:
            instructions += f" Use a {tone.lower()} tone."
        if style:
            instructions += f" Follow a {style.lower()} approach."

        instructions += " Provide a clear, well-structured response that fully addresses the goal."

        prompt_parts.append(instructions)

        return "\n\n".join(prompt_parts)

    def _is_spec_sufficient(self, spec: Dict[str, Any]) -> bool:
        """Check if the spec has enough information for a good prompt"""
        core_fields = ["goal", "audience"]
        return all(spec.get(field) for field in core_fields)

    def _calculate_spec_completeness(self, spec: Dict[str, Any]) -> float:
        """Calculate completeness percentage of the spec"""
        all_fields = ["goal", "audience", "tone", "style", "context", "constraints"]
        filled_fields = sum(1 for field in all_fields if spec.get(field))
        return filled_fields / len(all_fields)

# Global service instance
_askme_service = None

def get_askme_service() -> AskMeService:
    """Get the global AskMe service instance (singleton pattern)"""
    global _askme_service
    if _askme_service is None:
        _askme_service = AskMeService()
    return _askme_service

# Convenience functions
async def plan_questions(intent: str, spec: Dict[str, Any]) -> PlannerResult:
    """Convenience function to plan questions"""
    service = get_askme_service()
    return await service.plan_questions(intent, spec)

async def compose_prompt(spec: Dict[str, Any]) -> ComposerResult:
    """Convenience function to compose final prompt"""
    service = get_askme_service()
    return await service.compose_prompt(spec)