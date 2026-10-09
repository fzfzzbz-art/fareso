'use strict'
class TicTacToe {
  constructor(playerX, symbolO = 'o') {
    this.playerX = playerX
    this.playerO = null
    this._current = 'X'
    this.board = ['1','2','3','4','5','6','7','8','9']
    this.winner = null
    this.turns = 0
  }
  get currentTurn() { return this._current === 'X' ? this.playerX : this.playerO }
  render() { return this.board.slice() }
  turn(isO, index) {
    const symbol = isO ? 'O' : 'X'
    if (symbol !== this._current) return false
    if (index < 0 || index > 8) return false
    if (['X','O'].includes(this.board[index])) return false
    this.board[index] = symbol
    this.turns += 1
    this.checkWinner()
    this._current = this._current === 'X' ? 'O' : 'X'
    return true
  }
  checkWinner() {
    const lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
    for (const [a,b,c] of lines) {
      if (this.board[a] === this.board[b] && this.board[b] === this.board[c]) {
        this.winner = this.board[a] === 'X' ? this.playerX : this.playerO
        return this.winner
      }
    }
    return null
  }
}
module.exports = TicTacToe
