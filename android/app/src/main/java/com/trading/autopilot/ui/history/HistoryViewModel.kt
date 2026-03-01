package com.trading.autopilot.ui.history

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

data class HistoryUiState(
    val isLoading: Boolean = true,
    val error: String? = null,
    val trades: List<TradeResponse> = emptyList(),
    val metrics: MetricsResponse = MetricsResponse()
)

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(HistoryUiState())
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            repository.getTrades().onSuccess { trades ->
                _uiState.value = _uiState.value.copy(trades = trades)
            }
            repository.getMetrics().onSuccess { metrics ->
                _uiState.value = _uiState.value.copy(metrics = metrics)
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(error = e.message)
            }

            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }
}
