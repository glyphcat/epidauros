"""
物語におけるキャラクター原型の定義。
『The Writer's Journey』に基づくアーキタイプを定義する。
これらはシナリオ構造のTBoxにあたり、グラフ構造ではノードとして表現される。
"""

from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class CharacterArchetype(BaseModel):
    """
    キャラクターアーキタイプ
    """

    model_config = ConfigDict(frozen=True)

    # 基本情報
    id: str
    name_jp: str

    # 心理的・物語的機能
    # その役割の心理的側面
    psychological_function: str
    # 物語を前進させるための機能
    dramatic_function: str

    short_summary: str

    # アーキタイプの特徴
    core_traits: List[str]

    # 関連するシチュエーションアーキタイプ（idで紐付け）
    related_dramatic_situations: List[int]


# --- アーキタイプ定義 ---

HERO = CharacterArchetype(
    id="HERO",
    name_jp="ヒーロー（英雄）",
    # Psychological Function: The Ego's Search for Identity and Wholeness
    psychological_function=(
        "Represents the Freud's 'Ego'—the part of the personality that separates from "
        "the mother/tribe and considers itself distinct. The Hero's journey is the "
        "ego's search for identity and wholeness. Ultimately, the Hero must transcend "
        "the bounds of the ego to incorporate all separate parts of the personality "
        "into one complete, balanced 'Self.' They represent the human spirit in "
        "positive action and the soul in transformation."
    ),
    # Dramatic Function: Audience Identification, Growth, Action, and Sacrifice
    dramatic_function=(
        "1. Audience Identification: Acts as a 'window' into the story, allowing the "
        "audience to see the world through their eyes via a mix of universal drives "
        "and unique, even conflicting, traits. "
        "2. Growth/Learning: Usually the character who learns or grows the most, "
        "overcoming obstacles to gain new wisdom. "
        "3. Action: The most active person in the script; their will drives the story. "
        "Crucially, they must perform the decisive action at the climax. "
        "4. Sacrifice: The 'true mark' of a Hero (making holy). They must be willing "
        "to give up something of value—life, love, or a cherished vice—for an ideal. "
        "5. Dealing with Death: Shows us how to face actual or symbolic death, "
        "proving it can be survived or transcended."
    ),
    short_summary="The active protagonist who drives the story, undergoes inner transformation, and sacrifices personal desires for a higher ideal.",
    # Core Traits derived from the text
    core_traits=[
        "Ego-Transcendence",
        "Active Agency (Doing)",
        "Willingness to Sacrifice",
        "Universality vs. Originality",
        "Internalized Flaws (Humanization)",
        "Transformation/Arc",
        "Dealing with Mortality",
    ],
    # Related Situations: 9=Daring Enterprise, 20=Self-Sacrifice for an Ideal, 28=Obstacles to Love, 31=Conflict with a God
    related_dramatic_situations=[9, 20, 28, 31],
)

MENTOR = CharacterArchetype(
    id="MENTOR",
    name_jp="賢者（メンター）",
    # Psychological Function: The "Higher Self" and Inner Conscience
    psychological_function=(
        "Represents the 'Self' (the god within), the wiser and nobler part of the psyche "
        "that is connected to all things. It acts as a 'conscience' (like Jiminy Cricket) "
        "to guide the Hero when external protection is absent. It stands for the Hero's "
        "highest aspirations—what the Hero may become if they persist. Often related to "
        "the parent figure or a 'surrogate parent' who provides the moral and spiritual "
        "modeling that biological parents may lack."
    ),
    # Dramatic Function: Teaching, Gift-Giving, and Motivation
    dramatic_function=(
        "1. Teaching/Training: Preparing the Hero for the journey (e.g., drill instructors, professors). "
        "2. Gift-Giving (The Donor): Providing essential 'gifts' (magic weapons, keys, clues, advice) "
        "that must often be earned through sacrifice or commitment. "
        "3. Motivation: Helping the Hero overcome fear or giving a 'swift kick in the pants' to "
        "initiate the adventure. "
        "4. Planting: Introducing information or props that seem minor but become critical "
        "in the climax. "
        "5. Sexual Initiation: Acting as a 'shakti' to lead the lover toward experiencing the divine. "
        "Note: The Mentor must often be outgrown or 'internalized' as a code of ethics for "
        "the Hero to reach the next stage of development."
    ),
    short_summary="A wise guide or parental surrogate who provides training, essential gifts, and motivation to prepare the hero for the journey.",
    # Core Traits derived from the text
    core_traits=[
        "The Self/Higher Aspirations",
        "Conscience/Moral Code",
        "Donor (Provider of Gifts)",
        "Motivation & Initiation",
        "Parental Surrogate",
        "Shamanic Guide",
        "Internalized Ethics (Inner Mentor)",
    ],
    # Related Situations: 2=Deliverance (Rescue), 11=Enigma, 20=Self-Sacrifice for an Ideal
    related_dramatic_situations=[2, 11, 20],
)

THRESHOLD_GUARDIAN = CharacterArchetype(
    id="THRESHOLD_GUARDIAN",
    name_jp="境界の守護者",
    # Psychological Function: Internal Demons and Neuroses
    psychological_function=(
        "Represents the internal demons, neuroses, emotional scars, and self-limitations "
        "that hold back growth. On an outer level, they manifest as ordinary obstacles "
        "like prejudice or bad luck. Their appearance during a major life change is not "
        "necessarily to stop the Hero, but to test if the Hero is truly determined to "
        "accept the challenge of change. They symbolize the 'Resistance' one faces "
        "when attempting to break a status quo."
    ),
    # Dramatic Function: Testing and Signaling New Power
    dramatic_function=(
        "1. Testing: The primary function is to challenge the Hero with a puzzle, riddle, "
        "or combat to prove their worth. "
        "2. Options for Resolution: Heroes may bypass them by attacking, retreating, "
        "deceiving, bribing, or—most effectively—making an Ally of them. "
        "3. Incorporation: Successful Heroes learn to 'get into the skin' of the Guardian, "
        "absorbing their power or taking on their appearance (disguise) rather than "
        "uselessly trying to defeat a superior force. "
        "4. Signal of Progress: They serve as early indicators that new power or success "
        "is coming. They invite the Hero to see past surface impressions (the 'Stop' gesture) "
        "to the inner reality that welcomes the worthy."
    ),
    short_summary="Obstacles or lieutenants who test the hero's resolve and character, representing internal neuroses or external resistance to change.",
    # Core Traits derived from the text
    core_traits=[
        "Testing/Challenge",
        "Resistance as Strength",
        "Neuroses & Internal Demons",
        "Gatekeeping (Sentinels/Bouncers)",
        "Inversion (Presumed Enemy to Ally)",
        "Surface Appearance vs. Inner Reality",
        "Incorporation (Taking into the body)",
    ],
    # Related Situations: 9=Daring Enterprise (Test of Strength), 11=Enigma (Test of Wit)
    related_dramatic_situations=[9, 11],
)

HERALD = CharacterArchetype(
    id="HERALD",
    name_jp="使者（ヘラルド）",
    # Psychological Function: Call for Change
    psychological_function=(
        "Represents the psychological need for change. It is the 'inner voice' or "
        "a mysterious messenger (in dreams or reality) that announces we are ready "
        "to shift. Like a bell being struck, its vibrations spread until change "
        "becomes inevitable. It strikes a chord within the Hero that recognizes "
        "the current status quo is no longer sustainable."
    ),
    # Dramatic Function: Motivation and Getting the Story Rolling
    dramatic_function=(
        "1. Motivation: Providing the Hero with a reason to act, often by offering "
        "a challenge or an opportunity to overcome past shame or stagnation. "
        "2. Alerting: Signaling to both the Hero and the audience that the 'Ordinary World' "
        "is off-balance and adventure is imminent. "
        "3. News-Bearing: Acting as a delivery mechanism for critical information—a telegram, "
        "a phone call, or a treasure map—that shifts the Hero's trajectory. "
        "4. Versatility: The 'Herald mask' can be worn by anyone (Mentors, Villains, "
        "or even Allies) or manifested as a force of nature (storms, market crashes)."
    ),
    short_summary="A catalyst who delivers the 'call to adventure,' signaling that the status quo is no longer sustainable and change is imminent.",
    # Core Traits derived from the text
    core_traits=[
        "Call to Adventure",
        "Announcement of Change",
        "Catalyst for Action",
        "Shifting the Balance",
        "Inner/Outer Messenger",
        "Herald Mask (Flexible Role)",
        "Challenge/Opportunity Provider",
    ],
    # Related Situations: 9=Daring Enterprise (Call to Adventure), 11=Enigma (Unsolved Mystery)
    related_dramatic_situations=[9, 11],
)

SHAPESHIFTER = CharacterArchetype(
    id="SHAPESHIFTER",
    name_jp="シェイプシフター",
    # Psychological Function: The Anima/Animus and the Unreliable Other
    psychological_function=(
        "Represents the Jungian Anima (the female element in the male male psyche) "
        "or Animus (the male element in the female psyche). It reflects our "
        "internal confusion and inability to see the other person clearly through "
        "the masks they wear. It symbolizes the 'Protean' nature of human beings "
        "who dazzle, confuse, and shift to meet their own needs or to test the Hero. "
        "It manifests the repressed or unacknowledged parts of our own nature that "
        "we project onto others."
    ),
    # Dramatic Function: Seduction, Confusion, and Doubt
    dramatic_function=(
        "1. Bringing Doubt and Suspense: To keep the Hero (and audience) guessing "
        "about their true loyalty and nature. "
        "2. Seduction: Often manifests as the 'Femme Fatale' or 'Homme Fatale' who "
        "lures the Hero into dangerous situations or causes them to lose their strength. "
        "3. Catalyst for Revelation: By assuming disguises or telling lies, they force "
        "the Hero to look past surface appearances to find the truth. "
        "4. Mask-Wearing: This is a flexible 'mask' that can be worn by anyone. "
        "Heroes may become Shapeshifters to escape traps, and Villains may use "
        "it to trick the Hero."
    ),
    short_summary="An ambiguous character who creates doubt and suspense by shifting loyalties or appearances, mirroring the hero’s internal confusion.",
    # Core Traits derived from the text
    core_traits=[
        "Unreliability/Ambiguity",
        "Shifting Loyalty",
        "Protean (Readily taking many forms)",
        "Seduction and Charisma",
        "Disguise & Deception",
        "Mirroring the Hero's Desires/Fears",
        "The Fatale Aspect (Lethal Attraction)",
    ],
    # Related Situations: 11=Enigma, 18=Involuntary Crimes of Love, 24=Rivalry of Kinsmen, 33=Erroneous Judgment
    related_dramatic_situations=[11, 18, 24, 33],
)

SHADOW = CharacterArchetype(
    id="SHADOW",
    name_jp="影（シャドウ）",
    # Psychological Function: Repressed Feelings and the Psychotic Dark Side
    psychological_function=(
        "Represents the power of repressed feelings, deep trauma, or guilt hidden in the "
        "unconscious. While Threshold Guardians symbolize neuroses, the Shadow stands "
        "for psychoses that threaten to destroy the Hero. It is the 'shady part' of the "
        "Self—bad habits, old fears, and unexplored potential (like neglected creativity "
        "or affection) that becomes monstrous when denied. It reflects the 'roads not "
        "taken' and the dark energy of the psyche that must be brought into the light."
    ),
    # Dramatic Function: The Worthy Opponent and the Mirror of the Hero
    dramatic_function=(
        "1. Challenging the Hero: Providing a worthy opponent to force the Hero to rise "
        "to the challenge. A story is only as good as its villain. "
        "2. Manifesting Internal Conflict: The Hero can manifest a Shadow side through "
        "self-destructive acts, doubts, or the abuse of power. "
        "3. Humanization: Effective Shadows are humanized by a touch of goodness or "
        "vulnerability (e.g., a cold-hearted killer reading a letter from his daughter), "
        "making the Hero's choice to defeat them a true moral dilemma. "
        "4. Perspective: From the Shadow's point of view, they are the hero of their "
        "own myth, and the protagonist is their villain. "
        "5. Redemption/Vanquishing: External Shadows must be defeated, while internal "
        "Shadows can be redeemed by bringing them to consciousness."
    ),
    short_summary="A worthy opponent representing repressed psychoses or destructive potential; a dark mirror of the hero that must be defeated or redeemed.",
    # Core Traits derived from the text
    core_traits=[
        "Antagonism/Opposition",
        "Suppressed Potential",
        "Destructive Force",
        "Mirror of the Hero's Flaws",
        "Moral Complexity",
        "Self-Justified (The 'Right Man')",
        "Redeemability (Potential for Transformation)",
    ],
    # Related Situations: 3=Crime Pursued by Vengeance, 5=Pursuit, 30=Ambition, 34=Remorse
    related_dramatic_situations=[3, 5, 30, 34],
)

ALLY = CharacterArchetype(
    id="ALLY",
    name_jp="仲間（アライ）",
    # Psychological Function: Unused Parts of the Personality
    psychological_function=(
        "Represents the unexpressed or under-utilized parts of the personality that "
        "must be brought into action to complete the journey. They symbolize internal "
        "forces that come to our aid during a spiritual crisis. Psychologically, they "
        "remind us of actual relationships and support systems in our lives that "
        "provide the necessary 'extra brain power' or emotional grounding."
    ),
    # Dramatic Function: The Audience's Eye, Support, and Conscience
    dramatic_function=(
        "1. Audience Character: Asking questions the audience would ask, and providing "
        "a natural excuse for exposition about the 'Special World.' "
        "2. Functional Support: Providing vital services such as carrying messages, "
        "arranging disguises, or securing escape routes (The 'Helpful Servant' motif). "
        "3. Comic Relief and Foil: Offering humor or a contrasting worldview (e.g., "
        "Sancho Panza's realism vs. Don Quixote's idealism) to explore the Hero more deeply. "
        "4. Conscience: Monitoring the Hero's moral path and reacting when the Hero "
        "makes a moral error. "
        "5. Humanizing the Hero: Allowing the Hero to express fear, ignorance, or "
        "vulnerability that might otherwise seem inappropriate for the 'Hero' mask."
    ),
    short_summary="Supportive companions who provide functional help, moral conscience, and humanize the hero by acting as an audience proxy.",
    # Core Traits derived from the text
    core_traits=[
        "Sidekick/Companion",
        "Audience Proxy (Exposition)",
        "Moral Conscience",
        "Complementary Skills",
        "Non-human/Spirit Protectors",
        "Comic Foil",
        "Loyalty & Reliability",
    ],
    # Related Situations: 1=Supplication (Seeking Help), 2=Deliverance (Support), 21=Self-Sacrifice for Kindred
    related_dramatic_situations=[1, 2, 21],
)

TRICKSTER = CharacterArchetype(
    id="TRICKSTER",
    name_jp="トリックスター",
    # Psychological Function: Enemy of the Status Quo and Ego-Leveler
    psychological_function=(
        "Acts as a natural enemy of the status quo, cutting big egos down to size and "
        "bringing heroes and audiences back to earth. They point out folly and hypocrisy "
        "to bring about healthy change and transformation. Trickster energy often "
        "manifests through 'impish accidents' or slips of the tongue, alerting us to "
        "the absurdity of a stagnant psychological situation and providing much-needed "
        "perspective when we take ourselves too seriously."
    ),
    # Dramatic Function: Comic Relief and Catalyst
    dramatic_function=(
        "1. Comic Relief: Balancing heavy drama with moments of laughter to revive "
        "audience interest and prevent emotional exhaustion. "
        "2. Catalyst: Stirring up the existing system and affecting the lives of others "
        "while remaining largely unchanged themselves (e.g., Axel Foley). "
        "3. Subversion: Using quick wits and mischief to outwit physically stronger "
        "opponents or bypass Threshold Guardians. "
        "4. Spreading Strife: Sometimes stirring up trouble for its own sake to "
        "highlight the different perspectives (the 'red hat/blue hat' motif). "
        "5. Versatility: Can be a Hero, a Sidekick/Ally to the Hero or Shadow, or "
        "even turn into a deadly Shadow/adversary (e.g., Loki)."
    ),
    short_summary="A subversive catalyst who provides comic relief and cuts big egos down to size, using mischief to challenge the status quo.",
    # Core Traits derived from the text
    core_traits=[
        "Mischief & Deceit",
        "Quick Wits (Survival by Intelligence)",
        "Comic Relief",
        "Catalyst for Change",
        "Subversive/Anti-Status Quo",
        "Perspective Provider",
        "Boundary Crosser",
    ],
    # Related Situations: 11=Enigma, 13=Enmity of Kinsmen, 16=Madness, 32=Mistaken Jealousy
    related_dramatic_situations=[11, 13, 16, 32],
)


# --- 3. Collection for Global Access ---
ALL_CHARACTER_ARCHETYPES: List[CharacterArchetype] = [
    HERO,
    MENTOR,
    THRESHOLD_GUARDIAN,
    HERALD,
    SHAPESHIFTER,
    SHADOW,
    ALLY,
    TRICKSTER,
]

CHARACTER_ARCHETYPES_DICT: Dict[str, CharacterArchetype] = {
    archetype.id: archetype for archetype in ALL_CHARACTER_ARCHETYPES
}
