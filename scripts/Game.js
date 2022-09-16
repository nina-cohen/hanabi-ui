
const Card = require("./Card");

class Game {

    #deck;
    #playerTimestamps;
    #lastMove;
    #warningByPlayer;
    #moveCount = 0;
    #lastCardDeployed = 0;

    static INVALID_TIMESTAMP = -1;

    constructor() {
        this.initialize();
        this.#playerTimestamps = {};
        this.#warningByPlayer = {};
    }

    initialize() {
        // Generate a list of cards to sample from
        this.#deck = [];
        let cards = [];
        for (let color of Card.COLORS) {
            for (let rank of Card.RANKS) {
                cards.push(new Card(color, rank));
            }
        }
        // Now randomly sample from cards to build up the deck
        while (cards.length > 0) {
            let randomIndex = Math.floor(Math.random() * cards.length);
            this.#deck.push(cards[randomIndex]);
            cards.splice(randomIndex, 1);
        }
        this.#moveCount = 0;
        this.#lastMove = "0,0";
        this.#lastCardDeployed = 0;
    }

    stampPlayer(player) {
        this.#playerTimestamps[player] = Date.now();
        if (!this.#warningByPlayer.hasOwnProperty(player)) {
            this.#warningByPlayer[player] = 0;
        }
    }

    getPlayerTimestamp(player) {
        if (!this.#playerTimestamps.hasOwnProperty(player)) {
            console.log("Warning: A request was made for the timestamp of player " + player + " but this player is not"
            + " registered with this game.");
            return Game.INVALID_TIMESTAMP;
        }
        return this.#playerTimestamps[player];
    }

    getMoveCount() {
        return this.#moveCount;
    }

    incrementMoveCount() {
        this.#moveCount += 1;
    }

    setLastMove(lastMove) {
        this.#lastMove = lastMove;
    }

    hasPlayer(player) {
        return this.#playerTimestamps.hasOwnProperty(player);
    }

    getPlayers() {
        return Object.keys(this.#playerTimestamps);
    }

    bootPlayer(player) {
        delete this.#playerTimestamps[player];
        delete this.#warningByPlayer[player];
    }

    queueWarningForPlayer(player, warning) {
        this.#warningByPlayer[player] = warning;
    }

    getResponseMessage(player) {
        if (!this.#warningByPlayer.hasOwnProperty(player)) {
            console.log("Cannot get response message because warningByPlayer doesn't have a key for this player.");
            return;
        }
        return this.#moveCount + "," + this.#lastMove + "," + this.#lastCardDeployed + "," + this.#warningByPlayer[player];
    }

}

module.exports = Game
