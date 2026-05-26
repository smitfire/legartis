import { Pipe, PipeTransform } from '@angular/core';

import { clauseTypeColor } from './clause-type-color';
import type { ClauseType } from './models';

/**
 * Looks up the badge colour for a clause-type machine value. Pure; safe in
 * change-detection-heavy templates. Use as ``{{ ct | clauseTypeColor }}.bg``.
 */
@Pipe({ name: 'clauseTypeColor', standalone: true, pure: true })
export class ClauseTypeColorPipe implements PipeTransform {
  transform(value: ClauseType): { bg: string; fg: string } {
    return clauseTypeColor(value);
  }
}
