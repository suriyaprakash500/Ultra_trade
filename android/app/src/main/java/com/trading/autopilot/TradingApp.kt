package com.trading.autopilot

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.trading.autopilot.ui.briefing.BriefingScreen
import com.trading.autopilot.ui.dashboard.DashboardScreen
import com.trading.autopilot.ui.history.HistoryScreen
import com.trading.autopilot.ui.news.NewsScreen
import com.trading.autopilot.ui.settings.SettingsScreen
import com.trading.autopilot.ui.theme.*
import com.trading.autopilot.ui.trades.TradeIdeasScreen

/**
 * Navigation destinations.
 */
sealed class Screen(
    val route: String,
    val title: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    data object Dashboard : Screen("dashboard", "Home", Icons.Filled.Dashboard, Icons.Outlined.Dashboard)
    data object TradeIdeas : Screen("trade_ideas", "Ideas", Icons.Filled.AutoAwesome, Icons.Outlined.AutoAwesome)
    data object Briefing : Screen("briefing", "Briefing", Icons.Filled.WbSunny, Icons.Outlined.WbSunny)
    data object News : Screen("news", "News", Icons.Filled.Newspaper, Icons.Outlined.Newspaper)
    data object History : Screen("history", "History", Icons.Filled.History, Icons.Outlined.History)
    data object Settings : Screen("settings", "Settings", Icons.Filled.Settings, Icons.Outlined.Settings)
}

private val bottomNavItems = listOf(
    Screen.Dashboard,
    Screen.TradeIdeas,
    Screen.Briefing,
    Screen.News,
    Screen.History,
)

@Composable
fun TradingApp() {
    TradingAutopilotTheme {
        val navController = rememberNavController()
        val navBackStackEntry by navController.currentBackStackEntryAsState()
        val currentDestination = navBackStackEntry?.destination

        Scaffold(
            containerColor = DeepNavy,
            bottomBar = {
                NavigationBar(
                    containerColor = DarkSurface,
                    contentColor = TextPrimary,
                    tonalElevation = 0.dp
                ) {
                    bottomNavItems.forEach { screen ->
                        val selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true

                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                Icon(
                                    if (selected) screen.selectedIcon else screen.unselectedIcon,
                                    contentDescription = screen.title
                                )
                            },
                            label = {
                                Text(
                                    screen.title,
                                    fontSize = 10.sp,
                                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal
                                )
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = ElectricCyan,
                                selectedTextColor = ElectricCyan,
                                unselectedIconColor = TextMuted,
                                unselectedTextColor = TextMuted,
                                indicatorColor = ElectricCyan.copy(alpha = 0.1f)
                            )
                        )
                    }
                }
            }
        ) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = Screen.Dashboard.route,
                modifier = Modifier.padding(innerPadding)
            ) {
                composable(Screen.Dashboard.route) { DashboardScreen() }
                composable(Screen.TradeIdeas.route) { TradeIdeasScreen() }
                composable(Screen.Briefing.route) { BriefingScreen() }
                composable(Screen.News.route) { NewsScreen() }
                composable(Screen.History.route) { HistoryScreen() }
                composable(Screen.Settings.route) { SettingsScreen() }
            }
        }
    }
}
