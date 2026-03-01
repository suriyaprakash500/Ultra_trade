package com.trading.autopilot.ui.dashboard

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

data class DashboardUiState(
    val isLoading: Boolean = true,
    val error: String? = null,
    val portfolio: PortfolioResponse = PortfolioResponse(),
    val positions: List<PositionResponse> = emptyList(),
    val metrics: MetricsResponse = MetricsResponse(),
    val recentTrades: List<TradeResponse> = emptyList(),
    val killSwitchActive: Boolean = false,
    val killSwitchLoading: Boolean = false
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            val dashResult = repository.getDashboard()
            dashResult.onSuccess { dash ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    portfolio = dash.portfolio,
                    positions = dash.positions,
                    metrics = dash.metrics,
                    recentTrades = dash.recent_trades
                )
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "Failed to load dashboard"
                )
            }

            // Check kill switch status
            repository.getKillSwitchStatus().onSuccess {
                _uiState.value = _uiState.value.copy(killSwitchActive = it.active)
            }
        }
    }

    fun toggleKillSwitch() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(killSwitchLoading = true)

            if (_uiState.value.killSwitchActive) {
                repository.deactivateKillSwitch().onSuccess {
                    _uiState.value = _uiState.value.copy(
                        killSwitchActive = false,
                        killSwitchLoading = false
                    )
                }.onFailure {
                    _uiState.value = _uiState.value.copy(killSwitchLoading = false)
                }
            } else {
                repository.activateKillSwitch("Manual activation from Android app").onSuccess {
                    _uiState.value = _uiState.value.copy(
                        killSwitchActive = true,
                        killSwitchLoading = false
                    )
                    refresh() // Reload to see closed positions
                }.onFailure {
                    _uiState.value = _uiState.value.copy(killSwitchLoading = false)
                }
            }
        }
    }
}
