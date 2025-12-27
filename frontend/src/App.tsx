/**
 * 暗夜狼人杀 - 主应用入口
 */
import { GameBoard } from './components/GameBoard';
import { GameLobby } from './components/GameLobby';
import { RoleSelection } from './components/RoleSelection';
import { useGame } from './hooks/useGame';
import './App.css';

function App() {
    const {
        gameId,
        players,
        phase,
        round,
        currentSpeaker,
        humanPlayerId,
        humanRole,
        humanRoleName,
        roleDescription,
        result,
        speeches,
        systemMessages,
        actionRequired,
        isConnected,
        isGameRunning,
        hasConfirmedRole,
        thinkingPlayerId,
        votingThinkingPlayerIds,
        votedPlayerIds,
        nightActionMessage,
        announcement,
        teammates,
        createGame,
        startGame,
        performAction,
        connect,
        resetGame,
        clearAnnouncement,
        confirmRole
    } = useGame();

    // 根据游戏状态渲染不同界面
    const renderContent = () => {
        if (!isGameRunning) {
            return (
                <GameLobby
                    isConnected={isConnected}
                    gameCreated={!!gameId}
                    onConnect={connect}
                    onCreateGame={createGame}
                    onStartGame={startGame}
                />
            );
        }

        // 游戏开始后，如果没有确认角色，显示角色选择界面
        if (!hasConfirmedRole && humanRole) {
            return (
                <RoleSelection
                    assignedRole={humanRole}
                    roleDescription={roleDescription}
                    onConfirm={confirmRole}
                />
            );
        }

        return (
            <GameBoard
                players={players}
                phase={phase}
                round={round}
                currentSpeaker={currentSpeaker}
                thinkingPlayerId={thinkingPlayerId}
                votingThinkingPlayerIds={votingThinkingPlayerIds}
                votedPlayerIds={votedPlayerIds}
                nightActionMessage={nightActionMessage}
                humanPlayerId={humanPlayerId}
                humanRole={humanRole}
                humanRoleName={humanRoleName}
                roleDescription={roleDescription}
                speeches={speeches}
                systemMessages={systemMessages}
                actionRequired={actionRequired}
                gameResult={result}
                onSpeak={(content) => performAction('speak', { content })}
                onAction={(action, data) => performAction(action, data)}
                announcement={announcement}
                onClearAnnouncement={clearAnnouncement}
                onResetGame={resetGame}
                onBackToHome={() => window.location.reload()}
                isConnected={isConnected}
                teammates={teammates}
            />
        );
    };

    return (
        <div className="app-container">
            {renderContent()}
        </div>
    );
}

export default App;
