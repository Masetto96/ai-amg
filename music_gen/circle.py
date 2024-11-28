
class CircleOfFifthsFourths:
    def __init__(self):
        # Standard circle of fifths (clockwise)
        self.fifth_order = [
            'C', 'G', 'D', 'A', 'E', 'B', 'F♯/G♭', 'C♯/D♭', 
            'G♯/A♭', 'D♯/E♭', 'A♯/B♭', 'F'
        ]
        self.note_to_midi = {
        'C': 60,
        'C♯/D♭': 61,
        'D': 62,
        'D♯/E♭': 63,
        'E': 64,
        'F': 65,
        'F♯/G♭': 66,
        'G': 67,
        'G♯/A♭': 68,
        'A': 69,
        'A♯/B♭': 70,
        'B': 71
    }
        
        # Circle of fourths (counterclockwise) - reverse of fifths
        self.fourth_order = self.fifth_order[::-1]
    
    def _to_midi_pitch(self, note:str) -> int:
        return self.note_to_midi[note]
    
    def navigate_circle(self, start_note, steps, direction='fifths'):
        """
        Navigate around the circle of fifths or fourths.
        
        :param start_note: Starting note on the circle
        :param steps: Number of steps to move (can be float)
        :param direction: 'fifths' (clockwise) or 'fourths' (counterclockwise)
        :return: Destination note as midi pitch and note name (e.g. 60 is 'C')
        """
        # Select the appropriate circle based on direction
        current_circle = self.fifth_order if direction == 'fifths' else self.fourth_order
        
        # Find the index of the start note
        try:
            start_index = current_circle.index(start_note)
        except ValueError:
            raise ValueError(f"Note {start_note} not found in the circle")
        
        # Calculate the destination index
        # Use modulo to wrap around the circle
        dest_index = int(round((start_index + steps) % len(current_circle)))
        
        return self._to_midi_pitch(current_circle[dest_index]), current_circle[dest_index]