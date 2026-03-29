# src/core/prompts/extract_scenario_graph_v2.py

"""
グラフ抽出用のプロンプト定義（v2: メンション化＆ブロック構造対応版）
LLMへの指示を明確にするため、システムロール、ルール、手順、データのブロックに分割して管理します。
"""

# -------------------------------------------------------------------
# 1. System Role & Context
# -------------------------------------------------------------------
SYSTEM_ROLE_PROMPT = """
You are a professional screenwriter and an expert in data modeling, specifically utilizing Joseph Campbell's "The Hero's Journey" and Polti's "36 Dramatic Situations".
Your task is to analyze the provided movie plot and cast list to extract a structured narrative graph.
"""

# -------------------------------------------------------------------
# 2. Critical Rules (Guardrails)
# -------------------------------------------------------------------
CRITICAL_RULES_PROMPT = """
### [CRITICAL RULES]
1. [ID Mapping]: Use the provided IDs (e.g., $c1, $c2) strictly.
   - Set the `role_name` field of each node to its corresponding ID (e.g., "$c1").
   - DO NOT translate these IDs into names or other languages.
2. [Source Fidelity]: Base your analysis ONLY on the provided "Movie Plot".
   - If a relationship or character detail is not explicitly mentioned in the text, DO NOT include it in the graph.
   - Ignore any external knowledge or trivia you may have about the title.
3. [Isolated Nodes]: Characters in the "Cast List" that do not appear in the "Movie Plot" must have zero edges.
"""

# -------------------------------------------------------------------
# 3. Extraction Instructions
# -------------------------------------------------------------------
EXTRACTION_STEPS_PROMPT = """
### [Analysis Steps]
1. [Node Extraction]: Assign each character from the Cast List to exactly ONE fitting "Character Archetype" based on their narrative function in the plot.
2. [Edge Extraction]: Identify the most significant dramatic relationships between the characters. Assign each relationship to ONE fitting "Situation Archetype" (from the 36 Dramatic Situations).
   * Important: Refer to the "Related Situations" under each Character Archetype as hints, but the specific actions in the Plot ALWAYS take precedence.
3. [Evidence/Reason]: For the 'reason' field in edges, you MUST explicitly cite evidence from the plot using the character IDs (e.g., "$char_1 sacrificed themselves for $char_2").
4. [Setting]: Extract the `setting_period` (time period, e.g. "19th Century England", "Near Future") and `setting_location` (e.g. "London", "Deep Space"). If not mentioned, infer reasonably or put "Unknown".
5. [Language Consistency]: Even if the input plot is in Japanese, provide the `description`, `reason`, `setting_period`, and `setting_location` fields in English.
"""

# -------------------------------------------------------------------
# 4. Data Layout Template
# -------------------------------------------------------------------
# このテンプレートは、graph_generator.py 側で最終的にフォーマットされます。
# キャッシュ効率を高めるため、動的データ（actor_list, plot_text）は最後に配置します。
DATA_INPUT_TEMPLATE = """
## Character Archetype Definitions
{character_archetypes}

## Situation Archetype Definitions
{situation_archetypes}

## Input Data
### Cast List (Reference IDs)
{actor_list}

### Movie Plot to Analyze
{plot_text}
"""


# -------------------------------------------------------------------
# Helper: Full Prompt Assembler (Optional)
# -------------------------------------------------------------------
def build_full_extraction_prompt(
    character_archetypes_str: str,
    situation_archetypes_str: str,
    actor_list_str: str,
    plot_text: str,
) -> str:
    """
    各プロンプトブロックを結合し、最終的なLLM入力文字列を生成します。
    """
    prompt_blocks = [
        SYSTEM_ROLE_PROMPT.strip(),
        CRITICAL_RULES_PROMPT.strip(),
        EXTRACTION_STEPS_PROMPT.strip(),
        DATA_INPUT_TEMPLATE.strip().format(
            character_archetypes=character_archetypes_str,
            situation_archetypes=situation_archetypes_str,
            actor_list=actor_list_str,
            plot_text=plot_text,
        ),
    ]
    return "\n\n".join(prompt_blocks)
