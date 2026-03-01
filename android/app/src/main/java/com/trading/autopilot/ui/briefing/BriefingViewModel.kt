package com.trading.autopilot.ui.briefing

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trading.autopilot.data.model.MorningBriefingResponse
import com.trading.autopilot.data.repository.TradingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class BriefingUiState(
    val isLoading: Boolean = false,
    val isRunning: Boolean = false,
    val error: String? = null,
    val briefing: MorningBriefingResponse? = null
)

@HiltViewModel
class BriefingViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(BriefingUiState())
    val uiState: StateFlow<BriefingUiState> = _uiState.asStateFlow()

    fun runMorningRoutine() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRunning = true, error = null)

            repository.runMorningRoutine().onSuccess { result ->
                _uiState.value = _uiState.value.copy(
                    isRunning = false,
                    briefing = result
                )
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isRunning = false,
                    error = e.message ?: "Morning routine failed"
                )
            }
        }
    }

    fun loadExistingBriefing() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            repository.getMorningBriefing().onSuccess { result ->
                _uiState.value = _uiState.value.copy(isLoading = false, briefing = result)
            }.onFailure {
                _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }
}
