import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getSession,
  getSessionEvents,
  getSessions,
} from "../api/sessions";

import {
  ApiError,
  WS_BASE_URL,
} from "../api/client";

import type {
  AgentEvent,
  SessionDetailResponse,
  SessionListResponse,
  WebSocketConnectionStatus,
} from "../types";

interface UseAdminDashboardResult {
  dashboard: SessionListResponse;

  selectedSessionId: string | null;
  selectedSession: SessionDetailResponse | null;
  events: AgentEvent[];

  isLoadingSessions: boolean;
  isLoadingDetails: boolean;

  webSocketStatus: WebSocketConnectionStatus;

  error: string | null;
  lastUpdated: string | null;

  selectSession: (sessionId: string) => void;
  refreshDashboard: () => Promise<void>;
}

const emptyDashboard: SessionListResponse = {
  metrics: {
    total_sessions: 0,
    approved_refunds: 0,
    denied_refunds: 0,
    escalated_requests: 0,
    tool_failures: 0,
  },

  sessions: [],
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "The admin dashboard could not be loaded.";
}

function mergeEvent(
  existingEvents: AgentEvent[],
  newEvent: AgentEvent,
): AgentEvent[] {
  const eventAlreadyExists =
    existingEvents.some(
      (event) =>
        event.event_id === newEvent.event_id,
    );

  if (eventAlreadyExists) {
    return existingEvents;
  }

  return [...existingEvents, newEvent].sort(
    (firstEvent, secondEvent) =>
      firstEvent.event_id -
      secondEvent.event_id,
  );
}

export function useAdminDashboard():
  UseAdminDashboardResult {
  const [
    dashboard,
    setDashboard,
  ] = useState<SessionListResponse>(
    emptyDashboard,
  );

  const [
    selectedSessionId,
    setSelectedSessionId,
  ] = useState<string | null>(null);

  const [
    selectedSession,
    setSelectedSession,
  ] = useState<SessionDetailResponse | null>(
    null,
  );

  const [events, setEvents] = useState<
    AgentEvent[]
  >([]);

  const [
    isLoadingSessions,
    setIsLoadingSessions,
  ] = useState(true);

  const [
    isLoadingDetails,
    setIsLoadingDetails,
  ] = useState(false);

  const [
    webSocketStatus,
    setWebSocketStatus,
  ] = useState<WebSocketConnectionStatus>(
    "disconnected",
  );

  const [error, setError] = useState<
    string | null
  >(null);

  const [lastUpdated, setLastUpdated] =
    useState<string | null>(null);

  const detailRequestNumber = useRef(0);

  const selectedSessionIdReference =
    useRef<string | null>(null);

  const applySessionList = useCallback(
    (
      response: SessionListResponse,
    ): void => {
      setDashboard(response);
      setError(null);
      setLastUpdated(
        new Date().toISOString(),
      );

      const currentSessionId =
        selectedSessionIdReference.current;

      const currentSessionStillExists =
        response.sessions.some(
          (session) =>
            session.session_id ===
            currentSessionId,
        );

      const nextSessionId =
        currentSessionStillExists
          ? currentSessionId
          : (
              response.sessions[0]
                ?.session_id ?? null
            );

      if (
        nextSessionId === currentSessionId
      ) {
        return;
      }

      selectedSessionIdReference.current =
        nextSessionId;

      setSelectedSessionId(
        nextSessionId,
      );

      setSelectedSession(null);
      setEvents([]);
      setWebSocketStatus("disconnected");

      setIsLoadingDetails(
        nextSessionId !== null,
      );
    },
    [],
  );

  const loadSessionList = useCallback(
    async (): Promise<void> => {
      try {
        const response = await getSessions();

        applySessionList(response);
      } catch (loadError) {
        setError(
          getErrorMessage(loadError),
        );
      } finally {
        setIsLoadingSessions(false);
      }
    },
    [applySessionList],
  );

  const loadSelectedSession = useCallback(
    async (
      sessionId: string,
    ): Promise<void> => {
      const currentRequestNumber =
        detailRequestNumber.current + 1;

      detailRequestNumber.current =
        currentRequestNumber;

      try {
        const [
          sessionResponse,
          eventResponse,
        ] = await Promise.all([
          getSession(sessionId),
          getSessionEvents(sessionId),
        ]);

        if (
          detailRequestNumber.current !==
          currentRequestNumber
        ) {
          return;
        }

        if (
          selectedSessionIdReference.current !==
          sessionId
        ) {
          return;
        }

        setSelectedSession(
          sessionResponse,
        );

        setEvents(eventResponse);
        setError(null);
      } catch (loadError) {
        if (
          detailRequestNumber.current ===
          currentRequestNumber
        ) {
          setError(
            getErrorMessage(loadError),
          );
        }
      } finally {
        if (
          detailRequestNumber.current ===
          currentRequestNumber
        ) {
          setIsLoadingDetails(false);
        }
      }
    },
    [],
  );

  /*
   * Initial session-list load and polling.
   *
   * State updates happen in Promise callbacks rather than
   * synchronously through a state-changing function called
   * directly by the effect.
   */
  useEffect(() => {
    let effectIsActive = true;

    void getSessions()
      .then((response) => {
        if (!effectIsActive) {
          return;
        }

        applySessionList(response);
      })
      .catch((loadError: unknown) => {
        if (!effectIsActive) {
          return;
        }

        setError(
          getErrorMessage(loadError),
        );
      })
      .finally(() => {
        if (effectIsActive) {
          setIsLoadingSessions(false);
        }
      });

    const pollingInterval =
      window.setInterval(() => {
        void getSessions()
          .then((response) => {
            if (!effectIsActive) {
              return;
            }

            applySessionList(response);
          })
          .catch((loadError: unknown) => {
            if (!effectIsActive) {
              return;
            }

            setError(
              getErrorMessage(loadError),
            );
          });
      }, 5000);

    return () => {
      effectIsActive = false;

      window.clearInterval(
        pollingInterval,
      );
    };
  }, [applySessionList]);

  /*
   * Load the selected session.
   *
   * Again, updates occur only after the API Promise resolves.
   */
  useEffect(() => {
    if (!selectedSessionId) {
      return;
    }

    let effectIsActive = true;

    const currentRequestNumber =
      detailRequestNumber.current + 1;

    detailRequestNumber.current =
      currentRequestNumber;

    void Promise.all([
      getSession(selectedSessionId),
      getSessionEvents(
        selectedSessionId,
      ),
    ])
      .then(
        ([
          sessionResponse,
          eventResponse,
        ]) => {
          if (!effectIsActive) {
            return;
          }

          if (
            detailRequestNumber.current !==
            currentRequestNumber
          ) {
            return;
          }

          if (
            selectedSessionIdReference.current !==
            selectedSessionId
          ) {
            return;
          }

          setSelectedSession(
            sessionResponse,
          );

          setEvents(eventResponse);
          setError(null);
        },
      )
      .catch((loadError: unknown) => {
        if (!effectIsActive) {
          return;
        }

        if (
          detailRequestNumber.current ===
          currentRequestNumber
        ) {
          setError(
            getErrorMessage(loadError),
          );
        }
      })
      .finally(() => {
        if (!effectIsActive) {
          return;
        }

        if (
          detailRequestNumber.current ===
          currentRequestNumber
        ) {
          setIsLoadingDetails(false);
        }
      });

    return () => {
      effectIsActive = false;
    };
  }, [selectedSessionId]);

  /*
   * Open one WebSocket for the currently selected session.
   */
  useEffect(() => {
    if (!selectedSessionId) {
      return;
    }

    const encodedSessionId =
      encodeURIComponent(
        selectedSessionId,
      );

    const socket = new WebSocket(
      `${WS_BASE_URL}/ws/sessions/${encodedSessionId}`,
    );

    socket.onopen = () => {
      setWebSocketStatus("connected");
    };

    socket.onmessage = (
      messageEvent,
    ) => {
      try {
        const payload = JSON.parse(
          messageEvent.data as string,
        ) as {
          type?: string;
          events?: AgentEvent[];
          event?: AgentEvent;
          message?: string;
        };

        if (
          payload.type ===
            "SESSION_HISTORY" &&
          payload.events
        ) {
          setEvents(payload.events);
          return;
        }

        if (
          payload.type ===
            "AGENT_EVENT" &&
          payload.event
        ) {
          setEvents(
            (currentEvents) =>
              mergeEvent(
                currentEvents,
                payload.event as AgentEvent,
              ),
          );

          return;
        }

        if (
          payload.type ===
          "SESSION_UPDATED"
        ) {
          void loadSessionList();

          setIsLoadingDetails(true);

          void loadSelectedSession(
            selectedSessionId,
          );

          return;
        }

        if (
          payload.type === "ERROR" &&
          payload.message
        ) {
          setError(payload.message);
        }
      } catch {
        setError(
          "A live dashboard event could not be read.",
        );
      }
    };

    socket.onerror = () => {
      setWebSocketStatus(
        "disconnected",
      );
    };

    socket.onclose = () => {
      setWebSocketStatus(
        "disconnected",
      );
    };

    const pingInterval =
      window.setInterval(() => {
        if (
          socket.readyState ===
          WebSocket.OPEN
        ) {
          socket.send("ping");
        }
      }, 25000);

    return () => {
      window.clearInterval(
        pingInterval,
      );

      socket.close();
    };
  }, [
    selectedSessionId,
    loadSelectedSession,
    loadSessionList,
  ]);

  function selectSession(
    sessionId: string,
  ): void {
    detailRequestNumber.current += 1;

    selectedSessionIdReference.current =
      sessionId;

    setSelectedSessionId(sessionId);
    setSelectedSession(null);
    setEvents([]);
    setError(null);
    setIsLoadingDetails(true);
    setWebSocketStatus("disconnected");
  }

  async function refreshDashboard():
    Promise<void> {
    setIsLoadingSessions(true);

    await loadSessionList();

    const currentSessionId =
      selectedSessionIdReference.current;

    if (currentSessionId) {
      setIsLoadingDetails(true);

      await loadSelectedSession(
        currentSessionId,
      );
    }
  }

  return {
    dashboard,

    selectedSessionId,
    selectedSession,
    events,

    isLoadingSessions,
    isLoadingDetails,

    webSocketStatus,

    error,
    lastUpdated,

    selectSession,
    refreshDashboard,
  };
}