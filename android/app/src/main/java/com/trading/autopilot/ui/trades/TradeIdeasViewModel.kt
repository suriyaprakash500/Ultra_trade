package com.trading.autopilot.ui.trades

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trading.autopilot.data.model.*
import com.trading.autopilot.data.repository.TradingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TradeIdeasUiState(
    val isLoading: Boolean = false,
    val isGenerating: Boolean = false,
    val error: String? = null,
    val ideas: List<TradeIdea> = emptyList()
)

@HiltViewModel
class TradeIdeasViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(TradeIdeasUiState())
    val uiState: StateFlow<TradeIdeasUiState> = _uiState.asStateFlow()

    fun generateIdeas() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isGenerating = true, error = null)

            repository.getTradeIdeas().onSuccess { ideas ->
                _uiState.value = _uiState.value.copy(
                    isGenerating = false,
                    ideas = ideas
                )
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isGenerating = false,
                    error = e.message ?: "Failed to generate ideas"
                )
            }
        }
    }

    fun executeIdea(idea: TradeIdea) {
        viewModelScope.launch {
            val order = OrderRequest(
                symbol = idea.symbol,
                side = idea.side,
                quantity = if (idea.position_size > 0) idea.position_size else 1,
                reason = idea.reason,
                stop_loss = if (idea.stop_loss > 0) idea.stop_loss else null,
                take_profit = if (idea.take_profit > 0) idea.take_profit else null
            )
            repository.placeOrder(order).onSuccess {
                // Remove executed idea from list
                _uiState.value = _uiState.value.copy(
                    ideas = _uiState.value.ideas.filter { it != idea }
                )
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(error = e.message)
            }
        }
    }
}
