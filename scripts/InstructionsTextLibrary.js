
function getInstructionText(index, doesUserValueTooLittle) {
    let instructionText = "";
    switch (index) {
        case 0:
            if (doesUserValueTooLittle) {
                instructionText += "It is good to be cautious about playing cards when you are not sure that they are playable. " +
                    "However, when there are multiple life tokens left, it can be appropriate to take more risk in order to play " +
                    "more cards over the course of the game. <span class='boldSpan'>The AI thinks the team would be more successful if you were more willing " +
                    "to make plays when there are multiple life tokens left.</span>";
            } else {
                instructionText += "When there are multiple life tokens left, it sometimes makes sense to take a risk and " +
                    "attempt to play a card that might not be playable. However, <span class='boldSpan'>the AI thinks the team would be more successful " +
                    "if you waited to take these risks until you were more sure that the card is playable.</span>";
            }
            break;
        case 1:
            if (doesUserValueTooLittle) {
                instructionText += "It is good to be cautious about playing cards when you are not sure that they are playable, " +
                    "especially if there is only one life token left. However, it can benefit the team's average score across games " +
                    "if players are willing to make well timed, risky plays even with no life tokens to spare. <span class='boldSpan'>The AI thinks the team " +
                    "would be more successful if you were more willing to make plays even when there is only one life token remaining.</span>";
            } else {
                instructionText += "It sometimes makes sense to take a risk and attempt to play a card that might not be playable. " +
                    "However, when there is only one life token left, doing so is very risky since the next \"misplay\" will end the " +
                    "game. <span class='boldSpan'>The AI thinks the team would be more successful if you were more cautious about making plays when there " +
                    "is only one life token remaining.</span>";
            }
            break;
        case 2:
            if (doesUserValueTooLittle) {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in your " +
                    "hand), in the hopes that you will be more likely to play that card. The AI sometimes uses this convention, and <span class='boldSpan'>the " +
                    "AI believes the team would be more successful if you were more willing to play a card that the AI has singled out.</span>";
            } else {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in your " +
                    "hand), in the hopes that you will be more likely to play that card. The AI sometimes uses this convention, but not " +
                    "always. Sometimes a singled out card is not intended to be played. <span class='boldSpan'>The AI believes the team would be more successful " +
                    "if you were more cautious about playing a card that the AI has singled out.</span>";
            }
            break;
        case 3:
            if (doesUserValueTooLittle) {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in the " +
                    "other player's hand), in the hopes that they will be more likely to play that card. The AI sometimes uses this convention," +
                    "and <span class='boldSpan'>the AI believes the team would be more successful if you were more willing to give clues that single out a playable card in " +
                    "the AI's hand.</span>";
            } else {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in the " +
                    "other player's hand), in the hopes that they will be more likely to play that card. The AI sometimes uses this convention," +
                    "but the AI feels that you might be too focused on singling out playable cards and missing out on other opportunities " +
                    "(e.g. clues that give information about many cards in the AI's hands, or your own plays and discards). <span class='boldSpan'>The AI thinks " +
                    "the team would be more successful if you were a little less focused on singling out playable cards in the AI's hand.</span>";
            }
            break;
        case 4:
            if (doesUserValueTooLittle) {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in the " +
                    "other player's hand), in the hopes that they will be more likely to play that card. The AI sometimes uses this convention. " +
                    "Therefore, if you single out a card that is not playable, the AI might mistakenly attempt to play the card because the AI " +
                    "believed you intended for it to play that card. <span class='boldSpan'>The AI thinks the team would be more successful if you were a little less " +
                    "likely to give clues that single out cards that cannot be played.</span>";
            } else {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in the " +
                    "other player's hand), in the hopes that they will be more likely to play that card. The AI sometimes uses this convention, " +
                    "so it might feel risky to single out a card that cannot be played. However, the AI is carefully tracking information in the " +
                    "game that helps prevent this mistake, and <span class='boldSpan'>the AI believes the team would be more successful if you were more willing to " +
                    "give clues that single out cards even when they are not immediately playable.</span>";
            }
            break;
        case 5:
            if (doesUserValueTooLittle) {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in your " +
                    "hand), in the hopes that you will be more likely to play that card. The AI sometimes uses this convention, so it " +
                    "might feel risky to discard a card that the AI singled out. However, the AI trusts your ability to judge when a " +
                    "card in your hand should be discarded, and <span class='boldSpan'>the AI believes the team would be more successful if you were more willing " +
                    "to discard a card in your hand that was singled out, as long as you feel that it should be discarded.</span>";
            } else {
                instructionText += "Sometimes Hanabi players give clues that \"single out\" cards (highlighting only one card in your " +
                    "hand), in the hopes that you will be more likely to play that card. The AI sometimes uses this convention, so it " +
                    "can be disadvantageous to discard a card that the AI singled out (since it might have wanted you to play that card). " +
                    "<span class='boldSpan'>The AI believes the team would be more successful if you were less willing to discard cards that the AI has singled " +
                    "out in your hand.</span>";
            }
            break;
        case 6:
            if (doesUserValueTooLittle) {
                instructionText += "Based on clues it has received, the AI might believe a card in its hand could be playable " +
                    "when actually it cannot be played. In these cases, it can be beneficial for you to give clues that help " +
                    "inform the AI that a card in its hand cannot be played. <span class='boldSpan'>The AI believes the team would be more successful " +
                    "if you were to take more opportunities to give clues that help the AI realize its unplayable cards are " +
                    "not able to be played.</span>";
            } else {
                instructionText += "Based on clues it has received, the AI might believe a card in its hand could be playable " +
                    "when actually it cannot be played. In these cases, it can be beneficial for you to give clues that help " +
                    "inform the AI that a card in its hand cannot be played. However, the AI believes you might be focusing on " +
                    "this a little too much and passing up opportunities to give more informative clues or to make good plays " +
                    "and discards. <span class='boldSpan'>The AI believes the team would be more successful if you were to give fewer clues that " +
                    "focus on informing the AI of its unplayable cards.</span>";
            }
            break;
        case 7:
            if (doesUserValueTooLittle) {
                instructionText += "The AI felt that it was hard for it to make successful plays because it was not getting " +
                    "enough information about the cards it held, especially information about its playable cards." +
                    "<span class='boldSpan'>The AI thinks the team would be more successful if you were to give more priority to helping " +
                    "the AI make successful plays.</span>";
            } else {
                instructionText += "The AI felt that you were very focused on helping it make plays, and that you might have " +
                    "missed out on opportunities to make plays and discards from your hand, or to let the AI give clues about " +
                    "your hand. <span class='boldSpan'>The AI thinks the team would be more successful if you were less focused on giving clues " +
                    "about the playable cards in the AI's hand and more willing to make plays or discards.</span>";
            }
            break;
        case 8:
            if (doesUserValueTooLittle) {
                instructionText += "The AI felt that you sometimes had good information about playable cards that you held, " +
                    "yet you sometimes missed out on these opportunities to successfully play cards. <span class='boldSpan'>The AI thinks the team " +
                    "would be more successful if you were more focused on finding opportunities to play cards.</span>";
            } else {
                instructionText += "The AI felt that you were very focused on making plays from your hand and possibly " +
                    "missing out on opportunities to help the AI make plays. <span class='boldSpan'>The AI thinks the team would be more successful " +
                    "if you were less focused on making plays from your hand and took more opportunities to discard or to give " +
                    "clues to the AI that help it play and discard.</span>";
            }
            break;
        case 9:
            if (doesUserValueTooLittle) {
                instructionText += "When there are many information tokens available, it can be beneficial to give more clues " +
                    "before making plays or discards. <span class='boldSpan'>The AI thinks the team would be more successful if you were more willing " +
                    "to give clues when there are many information tokens available.</span>";
            } else {
                instructionText += "When there are few information tokens available, it can be important to try to make plays or " +
                    "discards rather than giving clues. If you don't know much about the cards you hold, it can be beneficial to " +
                    "discard so that the AI has information tokens in order to give you clues about the cards you hold. <span class='boldSpan'>The AI " +
                    "thinks the team would be more successful if you were more willing to make plays or discards when there are " +
                    "few information tokens available.</span>";
            }
            break;
        case 10:
            if (doesUserValueTooLittle) {
                instructionText += "If you are reasonably confident that a card in your hand is not the last of its kind, it can " +
                    "be beneficial to discard it in the hopes of playing a copy of that card later on in the game, and this is " +
                    "a good way to earn information tokens to allow more clues to be given. <span class='boldSpan'>The AI thinks " +
                    "the team would be more successful if you were more willing to discard cards that weren't the last of their " +
                    "kind (the discard table is helpful in making this judgment).</span>";
            } else {
                instructionText += "If you are reasonably confident that a card in your hand is not the last of its kind, it can " +
                    "be beneficial to discard it in the hopes of playing a copy of that card later on in the game. However " +
                    "if done too often this can risk discarding a card that has no other remaining copy in play, and this tends to " +
                    "hurt the final score. <span class='boldSpan'>The AI thinks the team would be more successful if you focused less on discarding " +
                    "cards that might not have been played yet.</span>";
            }
            break;
        case 11:
            if (doesUserValueTooLittle) {
                instructionText += "Sometimes you are holding a card that can never be played or has already been played. This card " +
                    "is the safest to discard and it is beneficial to discard such cards. <span class='boldSpan'>The AI thinks the team would be more " +
                    "successful if you paid closer attention to opportunities to discard these cards that won't ever be played.</span>";
            } else {
                instructionText += "Sometimes you are holding a card that can never be played or has already been played. This card " +
                    "is the safest to discard and it is beneficial to discard such cards. However, the AI thinks that you might have " +
                    "been too willing to discard these cards or missing opportunities to give useful clues or make plays. <span class='boldSpan'>The AI thinks " +
                    "the team would be more successful if you were less focused on discarding these types of cards.</span>";
            }
            break;
    }
    return instructionText;
}
