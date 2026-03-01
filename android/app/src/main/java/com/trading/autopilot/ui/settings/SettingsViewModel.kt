package com.trading.autopilot.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trading.autopilot.data.model.HealthResponse
import com.trading.autopilot.data.repository.TradingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val isConnected: Boolean = false,
    val isChecking: Boolean = false,
    val health: HealthResponse? = null,
    val kiteConnected: Boolean = false,
    val kiteLoginUrl: String = "",
    val error: String? = null
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init { checkConnection() }

    fun checkConnection() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isChecking = true, error = null)

            repository.getHealth().onSuccess { health ->
                _uiState.value = _uiState.value.copy(
                    isChecking = false,
                    isConnected = true,
                    health = health
                )
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isChecking = false,
                    isConnected = false,
                    error = "Cannot reach backend: ${e.message}"
                )
            }
        }
    }
}
