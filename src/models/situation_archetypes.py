"""
物語におけるシチュエーション原型の定義。
『The Thirty-Six Dramatic Situations』に基づくアーキタイプを定義する。
これらはシナリオ構造のTBoxにあたり、グラフ構造ではエッジとして表現される。
"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class SituationArchetype(BaseModel):
    """
    シチュエーションアーキタイプ

    """

    model_config = ConfigDict(frozen=True)

    # 基本情報
    id: str
    name_jp: str
    description: str
    short_summary: str  # プロンプトキャッシュ用の簡潔な英語定義

    # 局面成立に必要な要素（迫害者、救済者など）
    required_elements: List[str]

    # 階層構造を表現するパス（例：["カテゴリー", "大分類", "小分類（局面名）"]）
    # 前方一致の数で類似度を計算する
    hierarchy_path: List[str]


# --- 1. Hierarchy Vocabulary Definition ---


class Category(str, Enum):
    CONFLICT = "対立"
    COOPERATION = "協力"
    SACRIFICE = "犠牲"
    LOVE = "愛"
    CRIME = "犯罪"


class SubCategory(str, Enum):
    # 対立系
    PETITION = "哀願"
    ADVERSITY = "逆境"
    REBELLION = "反乱"
    ENTERPRISE = "冒険"
    ENIGMA = "謎"
    RIVALRY = "抗争"
    # 協力系
    RESCUE = "救出"
    ALLIANCE = "同盟"
    # 犠牲系
    LOSS = "喪失"
    DUTY = "義務"
    # 愛系
    PASSION = "情熱"
    MARITAL = "不倫・不貞"
    # 犯罪系
    REVENGE = "復讐"
    JUDICIAL = "司法・裁き"
    ABDUCTION = "略奪"
    MURDER = "殺意"


# --- 2. Situation Archetypes (01-36) ---
SIT_01 = SituationArchetype(
    id="SIT_01",
    name_jp="救済",
    description=(
        "A critical dynamic where a Suppliant, pursued by an inescapable Persecutor, "
        "reaches a Power (Redeemer). The drama hinges on the Power's moral choice to intervene. "
        "It mirrors the Hero's transition from helplessness to being mentored or protected."
    ),
    short_summary="A vulnerable character pursued by a persecutor reaches a powerful figure who chooses to provide rescue or redemption.",
    required_elements=[
        "Persecutor (Shadow)",
        "Suppliant (Hero/Victim)",
        "Power (Mentor)",
    ],
    hierarchy_path=[Category.CONFLICT, SubCategory.PETITION, "哀願と救済"],
)

SIT_02 = SituationArchetype(
    id="SIT_02",
    name_jp="災難からの救出",
    description=(
        "Focuses on the sudden intervention that averts catastrophe. An Unfortunate is "
        "trapped by a Threatener (often a monster or tyrant). The Rescuer's timely "
        "arrival provides a surge of hope and proves the Hero's or Mentor's capability."
    ),
    short_summary="A timely intervention where a rescuer saves an unfortunate character from an imminent threat or catastrophe.",
    required_elements=["Threatener (Shadow)", "Unfortunate (Ally)", "Rescuer (Hero)"],
    hierarchy_path=[Category.COOPERATION, SubCategory.RESCUE, "予期せぬ救出"],
)

SIT_03 = SituationArchetype(
    id="SIT_03",
    name_jp="復讐",
    description=(
        "The classic 'Revenge Pursuing Crime' arc. An Avenger seeks to balance the scales "
        "against a Guilty party for a past transgression against a Victim. This situation "
        "often turns the Hero into a relentless force, blurring the line between justice and Shadow."
    ),
    short_summary="An avenger seeks moral or physical retribution against a guilty party for a past crime against a victim.",
    required_elements=["Avenger (Hero)", "Guilty (Shadow)", "Victim (Memory)"],
    hierarchy_path=[Category.CRIME, SubCategory.REVENGE, "罪に対する復讐"],
)

SIT_04 = SituationArchetype(
    id="SIT_04",
    name_jp="親族間の復讐",
    description=(
        "A tragic escalation of revenge where the conflict is internal to the family unit. "
        "The Avenger must punish a Guilty relative, creating an agonizing clash between "
        "blood loyalty and moral duty. High potential for Shapeshifter revelations."
    ),
    short_summary="A tragic conflict where an avenger must punish a guilty relative, pitting family loyalty against moral justice.",
    required_elements=["Avenging_Kinsman", "Guilty_Kinsman", "Victim_Kinsman"],
    hierarchy_path=[Category.CRIME, SubCategory.REVENGE, "身内への復讐"],
)

SIT_05 = SituationArchetype(
    id="SIT_05",
    name_jp="追跡",
    description=(
        "A high-tension chase where a Fugitive flees from a relentless Punisher. "
        "The drama is built on the shrinking options of the escapee and the cold, "
        "unwavering momentum of the law or the enemy. Tests the Hero's resourcefulness."
    ),
    short_summary="A high-stakes chase where a fugitive attempts to escape from a relentless punisher or authority figure.",
    required_elements=["Punisher (Threshold_Guardian)", "Fugitive (Hero)"],
    hierarchy_path=[Category.CRIME, SubCategory.JUDICIAL, "逃亡と追跡"],
)

SIT_06 = SituationArchetype(
    id="SIT_06",
    name_jp="災害",
    description=(
        "The Hero or their world is overwhelmed by a superior force—natural disaster, "
        "political collapse, or divine wrath. It represents the ultimate external 'Resistance,' "
        "forcing the Hero into a state of total loss and eventual transformation."
    ),
    short_summary="A superior force or disaster overwhelms a character, leading to total defeat and potential transformation.",
    required_elements=["Victorious_Opponent (Shadow/Force)", "Defeated_Power (Hero)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "抗えぬ破滅"],
)

SIT_07 = SituationArchetype(
    id="SIT_07",
    name_jp="不運",
    description=(
        "A character suffers not for their sins, but due to pure Misfortune or the "
        "unprovoked Cruelty of a Shadow. It creates intense audience sympathy and "
        "establishes the 'Ordinary World' as a place that needs to be fixed or escaped."
    ),
    short_summary="An innocent character suffers due to pure misfortune or the unprovoked cruelty of a powerful opponent.",
    required_elements=["Innocent_Victim (Hero/Ally)", "Cruel_Opponent (Shadow)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "無垢な犠牲"],
)

SIT_08 = SituationArchetype(
    id="SIT_08",
    name_jp="反乱",
    description=(
        "A subordinate rises against a Tyrant. The drama stems from the defiance of "
        "authority and the moral justification of overthrowing a stagnant or oppressive system. "
        "The Hero often wears the 'Herald' mask for an entire movement."
    ),
    short_summary="A subordinate or conspirator rises to defy and overthrow an oppressive tyrant or authority figure.",
    required_elements=["Tyrant (Shadow)", "Conspirator (Hero/Ally)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.REBELLION, "権力への叛逆"],
)

SIT_09 = SituationArchetype(
    id="SIT_09",
    name_jp="不敵な試み",
    description=(
        "The Hero voluntarily enters a high-risk 'Enterprise' to achieve a monumental Goal. "
        "Whether it's a quest for treasure or a daring rescue, this situation defines "
        "the Hero's active agency and courage against an Adversary."
    ),
    short_summary="A hero voluntarily undertakes a high-risk mission to achieve a monumental goal against a strong adversary.",
    required_elements=["Bold_Leader (Hero)", "Adversary (Threshold_Guardian)", "Goal"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ENTERPRISE, "困難な冒険"],
)

SIT_10 = SituationArchetype(
    id="SIT_10",
    name_jp="略奪",
    description=(
        "The forced removal of a person or object from their rightful Guardian by an Abductor. "
        "This is the quintessential 'inciting incident' that pulls the Hero out of "
        "their comfort zone and into the Special World."
    ),
    short_summary="The forced abduction of a person or object from a guardian, often serving as a catalyst for adventure.",
    required_elements=["Abductor (Shadow)", "Abducted (Ally)", "Guardian (Hero)"],
    hierarchy_path=[Category.CRIME, SubCategory.ABDUCTION, "連れ去り"],
)

SIT_11 = SituationArchetype(
    id="SIT_11",
    name_jp="謎",
    description=(
        "A mental or spiritual challenge. A Seeker must solve a Riddle posed by an "
        "Interrogator to progress. Failure means death or stagnation; success grants "
        "the wisdom of the Mentor or passage past a Guardian."
    ),
    short_summary="A mental challenge where a seeker must solve a difficult riddle or problem posed by an interrogator.",
    required_elements=["Interrogator (Threshold_Guardian)", "Seeker (Hero)", "Problem"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ENIGMA, "真理の探究"],
)

SIT_12 = SituationArchetype(
    id="SIT_12",
    name_jp="獲得",
    description=(
        "The struggle for possession. A Solicitor tries to win a desired Object "
        "from a Refuser. This involves social maneuvering, theft, or persuasion, "
        "highlighting the friction between human desires and societal boundaries."
    ),
    short_summary="A struggle for possession where a solicitor attempts to gain a desired object from a refusing guardian.",
    required_elements=["Solicitor (Hero)", "Refuser (Threshold_Guardian)", "Object"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ENTERPRISE, "所有権の争い"],
)

SIT_13 = SituationArchetype(
    id="SIT_13",
    name_jp="親族間の敵意",
    description=(
        "Internal rot within a family. Kinsmen are pitted against each other by "
        "hatred, greed, or jealousy. This situation strips away the Ally mask from "
        "those the Hero should trust most, creating deep psychological scars."
    ),
    short_summary="A bitter conflict within a family where kinsmen are pitted against each other by hatred or greed.",
    required_elements=["Hatred_Kinsman (Shadow)", "Victim_Kinsman (Hero)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.RIVALRY, "血縁の不和"],
)

SIT_14 = SituationArchetype(
    id="SIT_14",
    name_jp="愛する者たちの抗争",
    description=(
        "Rivalry born of passion. Friends or lovers are forced to compete for a "
        "common Object or Beloved. The tragedy lies in the destruction of an Ally "
        "bond in favor of romantic or personal desire."
    ),
    short_summary="Friends or allies are forced to compete against each other for a common object of desire or love.",
    required_elements=["Rival_1 (Hero)", "Rival_2 (Ally)", "Object"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "愛の競合"],
)

SIT_15 = SituationArchetype(
    id="SIT_15",
    name_jp="不倫",
    description=(
        "The betrayal of a Marital or established bond for a new Beloved. "
        "It introduces the Shapeshifter dynamic into the domestic sphere, "
        "destroying the peace of the Ordinary World through deceit."
    ),
    short_summary="The betrayal of an established bond for a new beloved, disrupting the domestic world through deceit.",
    required_elements=["Adulterer (Shapeshifter)", "Betrayed_Partner", "Beloved"],
    hierarchy_path=[Category.LOVE, SubCategory.MARITAL, "裏切りの情愛"],
)

SIT_16 = SituationArchetype(
    id="SIT_16",
    name_jp="狂気",
    description=(
        "The loss of self. A character (often the Hero) is overtaken by Madness, "
        "committing acts they would never normally do. This represents the Shadow "
        "erupting from within, destroying the character’s identity and status."
    ),
    short_summary="A character loses their sanity and commits abnormal or harmful acts, representing an internal shadow eruption.",
    required_elements=["Madman (Shadow/Hero)", "Victim"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "精神の崩壊"],
)

SIT_17 = SituationArchetype(
    id="SIT_17",
    name_jp="不注意による過失",
    description=(
        "A fatal mistake caused by the Hero’s own hubris or Imprudence. "
        "This leads to a catastrophe that cannot be undone, serving as a "
        "harsh Mentor-like lesson in the consequences of one's actions."
    ),
    short_summary="A catastrophic and irreversible mistake caused by the hero's own hubris or lack of caution.",
    required_elements=["Imprudent (Hero)", "Victim (Ally)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "致命的な過失"],
)

SIT_18 = SituationArchetype(
    id="SIT_18",
    name_jp="無意識の恋愛過失",
    description=(
        "Tragedy arising from ignorance. Committing a forbidden act of passion "
        "without knowing the truth (e.g., Oedipus). It is the ultimate Shapeshifter "
        "trap where reality shifts after the act is committed."
    ),
    short_summary="A tragedy where a character unwittingly commits a forbidden act of passion due to ignorance of the truth.",
    required_elements=["Unwitting_Lover (Hero)", "Beloved"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "知らぬ間の背徳"],
)

SIT_19 = SituationArchetype(
    id="SIT_19",
    name_jp="知らぬ間に犯した親族の殺害",
    description=(
        "The Hero kills a Kinsman whom they failed to recognize. This is the "
        "pinnacle of irony and grief, where the Hero becomes their own Shadow "
        "through a lack of awareness or misidentification."
    ),
    short_summary="A character unintentionally kills a relative they failed to recognize, resulting in profound irony and grief.",
    required_elements=["Slayer (Hero)", "Unrecognized_Victim (Kinsman)"],
    hierarchy_path=[Category.CRIME, SubCategory.MURDER, "無知による凶行"],
)

SIT_20 = SituationArchetype(
    id="SIT_20",
    name_jp="理想のための自己犠牲",
    description=(
        "The Hero gives up their life, love, or safety for a noble Ideal. "
        "This is the final transformation of the Ego into the Self, making the "
        "Hero 'holy' through the act of sacrifice."
    ),
    short_summary="The hero sacrifices their life or safety for a noble ideal, achieving spiritual transcendence through the act.",
    required_elements=["Hero", "Ideal", "Sacrifice"],
    hierarchy_path=[Category.SACRIFICE, SubCategory.DUTY, "高潔な献身"],
)

SIT_21 = SituationArchetype(
    id="SIT_21",
    name_jp="親族のための自己犠牲",
    description=(
        "The Hero sacrifices their well-being to save or protect a Kinsman. "
        "It reinforces the Ally bond to the highest degree, proving that "
        "love for the tribe outweighs the instinct for self-preservation."
    ),
    short_summary="The hero sacrifices their well-being to protect a kinsman, proving loyalty to the family over self-preservation.",
    required_elements=["Hero", "Kinsman (Ally)", "Sacrifice"],
    hierarchy_path=[Category.SACRIFICE, SubCategory.DUTY, "血縁への献身"],
)

SIT_22 = SituationArchetype(
    id="SIT_22",
    name_jp="情熱のためのすべてを犠牲",
    description=(
        "The destructive power of obsession. A character throws away their reputation, "
        "honor, and safety for an all-consuming Passion. Here, the 'Beloved' functions "
        "as a lethal Shapeshifter or Shadow."
    ),
    short_summary="A character destroys their reputation and safety for an all-consuming obsession or forbidden passion.",
    required_elements=["Lover (Hero)", "Object_of_Passion", "Sacrifice"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "情熱による破滅"],
)

SIT_23 = SituationArchetype(
    id="SIT_23",
    name_jp="愛する者を犠牲にする必要",
    description=(
        "The ultimate test of Duty. The Hero must personally sacrifice a Beloved "
        "for a higher cause. This causes the deepest possible emotional scar and "
        "demands total transcendence of personal desire."
    ),
    short_summary="The hero is forced to sacrifice a beloved person for a higher duty or cause, causing deep trauma.",
    required_elements=["Hero", "Beloved_Victim (Ally)", "Duty"],
    hierarchy_path=[Category.SACRIFICE, SubCategory.DUTY, "非情な選択"],
)

SIT_24 = SituationArchetype(
    id="SIT_24",
    name_jp="優劣の争い",
    description=(
        "A rivalry defined by social or power disparity. An Inferior challenges a "
        "Superior for an Object or status. It highlights the struggle against "
        "Threshold Guardians of the social order."
    ),
    short_summary="A rivalry where an inferior character challenges a superior one for power, status, or an object.",
    required_elements=["Superior (Shadow)", "Inferior (Hero)", "Object"],
    hierarchy_path=[Category.CONFLICT, SubCategory.RIVALRY, "格差の抗争"],
)

SIT_25 = SituationArchetype(
    id="SIT_25",
    name_jp="姦通",
    description=(
        "A complex triangle of Deception. The drama focuses on the tension between "
        "the Adulterer, the Deceived Partner, and the Unfaithful party. A situation "
        "where everyone wears a Shapeshifter mask."
    ),
    short_summary="A deceptive romantic triangle involving an adulterer, a deceived partner, and an unfaithful party.",
    required_elements=["Adulterer", "Deceived_Partner", "Unfaithful_Party"],
    hierarchy_path=[Category.LOVE, SubCategory.MARITAL, "三角関係の破綻"],
)

SIT_26 = SituationArchetype(
    id="SIT_26",
    name_jp="恋愛の罪",
    description=(
        "A crime—such as murder or theft—committed specifically to enable or "
        "protect a forbidden love. The 'Love' category crosses over into the "
        "'Crime' category, as passion overrides morality."
    ),
    short_summary="A crime committed specifically to enable, protect, or fulfill a forbidden and all-consuming love.",
    required_elements=["Lover (Hero/Shadow)", "Beloved", "Victim"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "愛ゆえの罪"],
)

SIT_27 = SituationArchetype(
    id="SIT_27",
    name_jp="愛する者の不名誉の発見",
    description=(
        "The moment the Hero discovers a shameful secret or betrayal by their Beloved. "
        "It is the 'Shapeshifter moment' where the internal image of the lover "
        "shatters, leading to grief or revenge."
    ),
    short_summary="The hero discovers a shameful secret or betrayal by their beloved, shattering their trust and perception.",
    required_elements=["Discoverer (Hero)", "Guilty_One (Shapeshifter/Ally)"],
    hierarchy_path=[Category.LOVE, SubCategory.MARITAL, "幻滅"],
)

SIT_28 = SituationArchetype(
    id="SIT_28",
    name_jp="恋愛の障害",
    description=(
        "Two lovers are separated by external forces—war, family feuds, or social "
        "rank. The conflict is not between the lovers, but between the couple and "
        "the world (Threshold Guardians)."
    ),
    short_summary="External forces or societal obstacles prevent two lovers from being together, despite their mutual desire.",
    required_elements=["Lover_1", "Lover_2", "Obstacle (Force/Shadow)"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "成就せぬ愛"],
)

SIT_29 = SituationArchetype(
    id="SIT_29",
    name_jp="敵への愛",
    description=(
        "The Hero falls in love with the Enemy. This creates the ultimate internal "
        "conflict, as the Beloved is also a representative of the Shadow group, "
        "forcing a choice between heart and tribe."
    ),
    short_summary="A character falls in love with a member of the enemy group, creating an intense internal conflict of loyalty.",
    required_elements=["Lover (Hero)", "Beloved_Enemy (Shadow)"],
    hierarchy_path=[Category.LOVE, SubCategory.PASSION, "禁断の恋慕"],
)

SIT_30 = SituationArchetype(
    id="SIT_30",
    name_jp="野心",
    description=(
        "A character is consumed by a desire for power or fame, leading to the "
        "destruction of Rivals and moral compromise. The Ambitious Person is "
        "a Hero who is rapidly turning into a Shadow."
    ),
    short_summary="An all-consuming desire for power or fame that leads to moral compromise and the destruction of rivals.",
    required_elements=["Ambitious_Person (Hero/Shadow)", "Coveted_Object", "Adversary"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ENTERPRISE, "野望と闘争"],
)

SIT_31 = SituationArchetype(
    id="SIT_31",
    name_jp="神との闘争",
    description=(
        "The struggle against Destiny or higher supernatural powers. The Mortal "
        "challenges the Immortal order, representing the Ego's defiance against "
        "the inevitable forces of the universe."
    ),
    short_summary="A mortal character struggles against destiny, fate, or superior supernatural powers in an act of defiance.",
    required_elements=["Mortal (Hero)", "Immortal_Power (Shadow)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "運命への抗い"],
)

SIT_32 = SituationArchetype(
    id="SIT_32",
    name_jp="誤解による嫉妬",
    description=(
        "Jealousy fueled by a Deceiver's lies or a false impression. The Hero "
        "attacks an innocent Ally based on a mistake of perception. A masterclass "
        "in Trickster influence."
    ),
    short_summary="Jealousy fueled by deception or false impressions, leading a character to attack an innocent ally.",
    required_elements=[
        "Jealous_One (Hero)",
        "Object_of_Jealousy",
        "Deceiver (Trickster)",
    ],
    hierarchy_path=[Category.CONFLICT, SubCategory.RIVALRY, "猜疑の連鎖"],
)

SIT_33 = SituationArchetype(
    id="SIT_33",
    name_jp="判断の誤り",
    description=(
        "A tragic mistake where a character misjudges a situation or person, "
        "leading to unintended harm. It highlights the fallibility of the Hero "
        "and the tragic nature of human perception."
    ),
    short_summary="A tragic mistake in judgment or perception that leads to unintended harm and unfortunate consequences.",
    required_elements=["Mistaken_One (Hero)", "Victim_of_Error (Ally)"],
    hierarchy_path=[Category.CONFLICT, SubCategory.ADVERSITY, "誤認の悲劇"],
)

SIT_34 = SituationArchetype(
    id="SIT_34",
    name_jp="後悔",
    description=(
        "Remorse for a past crime or betrayal. The character is haunted by the "
        "Shadow of their former self, seeking atonement or being destroyed by "
        "the memory of the Victim."
    ),
    short_summary="A character is haunted by remorse for past crimes, seeking atonement or being consumed by guilt.",
    required_elements=["Remorseful_One (Hero)", "Victim (Memory)"],
    hierarchy_path=[Category.CRIME, SubCategory.REVENGE, "過去の悔恨"],
)

SIT_35 = SituationArchetype(
    id="SIT_35",
    name_jp="再会",
    description=(
        "The resolution of long-standing separation. Lost friends, lovers, or kin "
        "find each other again. It is a moment of deep emotional healing and "
        "the restoration of an Ally bond."
    ),
    short_summary="The emotional resolution of a long separation where lost friends, lovers, or kin finally reunite.",
    required_elements=["Seeker (Hero)", "Found_One (Ally)"],
    hierarchy_path=[Category.COOPERATION, SubCategory.ALLIANCE, "絆の再生"],
)

SIT_36 = SituationArchetype(
    id="SIT_36",
    name_jp="愛する者の喪失",
    description=(
        "The finality of death. The Survivor must process the grief of a Deceased "
        "loved one. It marks the ultimate Threshold, where the Hero must find "
        "a way to live without their most vital Ally."
    ),
    short_summary="The finality of death and the resulting grief as a survivor struggles to live without a loved one.",
    required_elements=["Survivor (Hero)", "Deceased (Ally)"],
    hierarchy_path=[Category.SACRIFICE, SubCategory.LOSS, "永遠の別れ"],
)

# --- 3. Collection for Global Access ---
ALL_SITUATIONS_ARCHETYPES: List[SituationArchetype] = [
    eval(f"SIT_{str(i).zfill(2)}") for i in range(1, 37)
]

SITUATION_ARCHETYPES_DICT: Dict[int, SituationArchetype] = {
    i: eval(f"SIT_{str(i).zfill(2)}") for i in range(1, 37)
}
